from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

import attr
from cryptoxlib.Pair import Pair

from .utilities import epoch_ms_to_datetime


class Exchange(Enum):
    binance = 1
    bitforex = 2


@attr.s(auto_attribs=True)
class Trade:
    """
    The order of attributes must match the order of the Postgres columns.
    """

    exchange: Exchange
    time: datetime
    id: int
    ingestion_time: datetime
    price: Decimal
    quantity: Decimal
    pair: str


def as_postgres_row(trade: Trade) -> tuple:
    """
    The exchange enum is not inserted.
    """

    return attr.astuple(trade)[:-1]


@attr.s(auto_attribs=True)
class BinanceTrade(Trade):
    """
    The order of attributes must match the order of the Postgres columns.

    https://github.com/binance-exchange/binance-official-api-docs/blob/master/web-socket-streams.md#aggregate-trade-streams

    {
      "e": "trade",     // Event type
      "E": 123456789,   // Event time
      "s": "BNBBTC",    // Symbol
      "t": 12345,       // Trade ID
      "p": "0.001",     // Price
      "q": "100",       // Quantity
      "b": 88,          // Buyer order ID
      "a": 50,          // Seller order ID
      "T": 123456785,   // Trade time
      "m": true,        // Is the buyer the market maker?
      "M": true         // Ignore
    }

    """

    buyer_market_maker: bool

    buyer_order_id: Optional[int] = None
    seller_order_id: Optional[int] = None
    trade_time: Optional[datetime] = None
    quote_quantity: Optional[Decimal] = None
    best_match: Optional[bool] = None

    exchange: Exchange = Exchange.binance

    @classmethod
    def from_websocket_api(cls, pair: Pair, response: dict) -> "BinanceTrade":
        return cls(
            time=epoch_ms_to_datetime(response["E"]),
            id=int(response["t"]),
            ingestion_time=datetime.now(),
            price=Decimal(response["p"]),
            quantity=Decimal(response["q"]),
            pair=str(pair),
            buyer_market_maker=bool(response["m"]),
            buyer_order_id=int(response["b"]),
            seller_order_id=int(response["a"]),
            trade_time=epoch_ms_to_datetime(response["T"]),
        )

    @classmethod
    def from_http_api(cls, pair: Pair, response: dict) -> "BinanceTrade":
        return cls(
            time=epoch_ms_to_datetime(response["time"]),
            id=int(response["id"]),
            ingestion_time=datetime.now(),
            price=Decimal(response["price"]),
            quantity=Decimal(response["qty"]),
            pair=str(pair),
            buyer_market_maker=bool(response["isBuyerMaker"]),
            quote_quantity=Decimal(response["quoteQty"]),
            best_match=bool(response["isBestMatch"]),
        )


@attr.s(auto_attribs=True)
class BitforexTrade(Trade):
    """
    The order of attributes must match the order of the Postgres columns.

    https://github.com/githubdev2020/API_Doc_en/wiki/Trading-record-information

    {
        "success": true,
        "data": [{
            "amount": 1,
            "direction": 1,
            "price": 990,
            "tid": "8076",
            "time": 1516628489676
        }]
    }
    """

    direction: int

    exchange: Exchange = Exchange.bitforex

    @classmethod
    def from_websocket_api(cls, pair: Pair, response: dict) -> "BitforexTrade":
        return cls(
            time=epoch_ms_to_datetime(response["time"]),
            id=int(response["tid"]),
            ingestion_time=datetime.now(),
            price=Decimal(response["price"]),
            quantity=Decimal(response["amount"]),
            pair=str(pair),
            direction=int(response["direction"]),
        )
