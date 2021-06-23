# Slide-Puzzle - Spring 2020

This project was made as for the Final Project for a Discrete Mathmatics for Computing course.
The task was to demonstrate some sort of algorithm visually using Python. I chose a slide puzzle
solver using the A* algorithm. 

At each iteration of its main loop, A* needs to determine which of its paths to extend. It does 
so based on the cost of the path and an estimate of the cost required to extend the path all the
way to the goal. Specifically, A* selects the path that minimizes
    f(n) = g(n) + h(n)
where n is the next node on the path, g(n) is the cost of the path from the start node to n, and 
h(n) is a heuristic function that estimates the cost of the cheapest path from n to the goal. A* 
terminates when the path it chooses to extend is a path from start to goal or if there are no paths
eligible to be extended. The heuristic function is problem-specific. If the heuristic function is 
admissible, meaning that it never overestimates the actual cost to get to the goal, A* is guaranteed 
to return a least-cost path from start to goal.
