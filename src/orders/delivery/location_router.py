import time
from itertools import permutations
from math import inf
from aws_lambda_powertools import Logger


class TravelPlanner:

    def calculate_distance(self, point1, point2):
        """
        Calculate the Euclidean distance between two points.
        """
        lat1, lon1 = float(point1["latitude"]), float(point1["longitude"])
        lat2, lon2 = float(point2["latitude"]), float(point2["longitude"])
        return ((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2) ** 0.5

    def total_distance(self, path, locations):
        """
        Calculate the total distance of a given path.
        """
        distance = 0
        for i in range(len(path) - 1):
            distance += self.calculate_distance(
                locations[path[i]], locations[path[i + 1]]
            )
        return distance

    def find_shortest_path(self, locations, start_point):
        """
        Find the shortest path to visit all locations using the Travelling Salesman Problem algorithm.
        """
        locations.append(start_point)
        num_locations = len(locations)
        locations_indices = list(range(num_locations))
        logger = Logger()

        start_time = time.time()
        logger.info(
            f"Started shortest path at {start_time}"
        )

        start_index = next(
            (
                index
                for index, loc in enumerate(locations)
                if loc["latitude"] == start_point["latitude"]
                and loc["longitude"] == start_point["longitude"]
            ),
            None,
        )

        if start_index is not None:
            locations_indices.remove(start_index)
            locations_indices.insert(0, start_index)

            all_permutations = permutations(locations_indices[1:])

            min_distance = inf
            shortest_path = None

            for path in all_permutations:
                path = (locations_indices[0],) + path
                distance = self.total_distance(path, locations)
                if distance < min_distance:
                    min_distance = distance
                    shortest_path = path

            ordered_locations = [locations[i] for i in shortest_path]
            for index, order in enumerate(ordered_locations):
                order["delivery_sequence"] = index
            # We need to remove starting point from the list, so there is no confusions in frontend
            ordered_locations.pop(0)

            end_time = time.time()
            execution_time = end_time - start_time
            logger.info(f"Execution time: {execution_time} seconds")

            return ordered_locations
        else:
            raise ValueError("Start point not found in locations list")
