from dataclasses import dataclass


@dataclass
class WindowBounds:
    south_lat: float = 0.0
    north_lat: float = 0.0
    west_lng: float = 0.0
    east_lng: float = 0.0

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
