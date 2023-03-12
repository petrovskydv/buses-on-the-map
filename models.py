from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel


class WindowBounds(BaseModel):
    south_lat: float
    north_lat: float
    west_lng: float
    east_lng: float

    def update(self, new):
        for key, value in new.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def is_inside(self, lat, lng):
        is_lat_in_bounds = self.north_lat > lat > self.south_lat
        is_lng_in_bounds = self.east_lng > lng > self.west_lng
        return all((is_lat_in_bounds, is_lng_in_bounds))


@dataclass
class Bus:
    busId: str
    lat: float
    lng: float
    route: str


class BrowserMsg(BaseModel):
    msgType: Literal['newBounds']
    data: WindowBounds
