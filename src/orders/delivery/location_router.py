class TravelPlanner:
    def calculate_distance(self, point1, point2):
        """
        Calculate the Euclidean distance between two points
        """
        lat1, lon1 = float(point1["latitude"]), float(point1["longitude"])
        lat2, lon2 = float(point2["latitude"]), float(point2["longitude"])
        return ((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2) ** 0.5

    def find_shortest_path(self, locations, start_point):
        """
        Find the shortest path to visit all locations using the nearest neighbor heuristic
        """
        num_locations = len(locations)
        if num_locations == 0:
            return []

        unvisited = locations[:]
        current_location = start_point
        path = [start_point]
        total_distance = 0

        while unvisited:
            nearest_location = min(
                unvisited,
                key=lambda loc: self.calculate_distance(current_location, loc),
            )
            total_distance += self.calculate_distance(
                current_location, nearest_location
            )
            current_location = nearest_location
            path.append(nearest_location)
            unvisited.remove(nearest_location)

        for index, location in enumerate(path):
            location["delivery_sequence"] = index

        return path
