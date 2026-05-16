from unittest import TestCase

from src.orders.delivery.location_router import TravelPlanner


class TestTravelPlanner(TestCase):

    def setUp(self):
        self.planner = TravelPlanner()
        self.start = {"latitude": 20.7257943, "longitude": -103.3792193}

    def test_find_shortest_path_empty_locations_returns_empty(self):
        result = self.planner.find_shortest_path([], self.start)
        self.assertEqual(result, [])

    def test_find_shortest_path_single_location(self):
        locations = [
            {
                "id": "1",
                "latitude": 20.71,
                "longitude": -103.38,
                "delivery_date": "2024-01-08",
            }
        ]
        result = self.planner.find_shortest_path(locations, self.start)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["delivery_sequence"], 1)

    def test_find_shortest_path_assigns_delivery_sequence(self):
        locations = [
            {
                "id": "a",
                "latitude": 20.70,
                "longitude": -103.37,
                "delivery_date": "2024-01-08",
            },
            {
                "id": "b",
                "latitude": 20.69,
                "longitude": -103.36,
                "delivery_date": "2024-01-08",
            },
            {
                "id": "c",
                "latitude": 20.68,
                "longitude": -103.35,
                "delivery_date": "2024-01-08",
            },
        ]
        result = self.planner.find_shortest_path(locations, self.start)
        sequences = sorted(loc["delivery_sequence"] for loc in result)
        self.assertEqual(sequences, [1, 2, 3])

    def test_find_shortest_path_visits_all_locations(self):
        locations = [
            {
                "id": str(i),
                "latitude": 20.70 + i * 0.01,
                "longitude": -103.37,
                "delivery_date": "2024-01-08",
            }
            for i in range(5)
        ]
        result = self.planner.find_shortest_path(locations, self.start)
        self.assertEqual(len(result), 5)

    def test_calculate_distance_same_point_is_zero(self):
        point = {"latitude": 20.7, "longitude": -103.3}
        self.assertEqual(self.planner.calculate_distance(point, point), 0.0)

    def test_calculate_distance_different_points(self):
        p1 = {"latitude": 20.7, "longitude": -103.3}
        p2 = {"latitude": 20.8, "longitude": -103.3}
        dist = self.planner.calculate_distance(p1, p2)
        self.assertAlmostEqual(dist, 0.1, places=5)

    def test_find_shortest_path_nearest_neighbor_order(self):
        # Start near "close", far from "far"
        start = {"latitude": 20.70, "longitude": -103.37}
        close = {
            "id": "close",
            "latitude": 20.71,
            "longitude": -103.37,
            "delivery_date": "2024-01-08",
        }
        far = {
            "id": "far",
            "latitude": 20.80,
            "longitude": -103.37,
            "delivery_date": "2024-01-08",
        }
        result = self.planner.find_shortest_path([far, close], start)
        self.assertEqual(result[0]["id"], "close")
        self.assertEqual(result[1]["id"], "far")
