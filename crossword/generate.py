import sys

from crossword import *
from copy import deepcopy
from random import choice


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        w, h = draw.textsize(letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        domain_copy = deepcopy(self.domains)

        for var in domain_copy:
            for word in domain_copy[var]:
                if len(word) != var.length:
                    self.domains[var].remove(word)


    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        revised = False

        if self.crossword.overlaps[x, y]:

            x_overlap_index, y_overlap_index = self.crossword.overlaps[x, y]
            x_copy = self.domains[x].copy()

            for x_word in x_copy:
                is_arc_consistent = False

                for y_word in self.domains[y]:

                    if x_word[x_overlap_index] == y_word[y_overlap_index]:
                        is_arc_consistent = True
                        
                if not is_arc_consistent:
                    self.domains[x].remove(x_word)
                    revised = True
        
        return revised


    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        queue = list()
        if arcs:
            queue = arcs
        else:
            for x in self.domains:
                for y in self.crossword.neighbors(x):
                    queue.append((x, y))
        
        while len(queue) != 0:
            x, y = queue.pop(0)
            if self.revise(x, y):
                if len(self.domains[x]) == 0:
                    return False
                for z in self.crossword.neighbors(x):
                    if z != y:
                        queue.append((z, x))

        return True
        

    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        # Every variable in the crossword is in assignment
        for var in self.crossword.variables:
            if var not in assignment or assignment[var] == None:
                return False

        return True

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """

        checked = []
        for var in assignment:

            # Check that each word is the proper length for the corresponding var
            if var.length != len(assignment[var]):
                return False
            
            # Check for conflicting characters between neighbors
            for neighbor in self.crossword.neighbors(var):

                # avoid repeating for combinations already checked
                if (var, neighbor) in checked or (neighbor, var) in checked:
                    continue

                x_overlap_index, y_overlap_index = self.crossword.overlaps[var, neighbor]
                if neighbor in assignment:
                    if assignment[var][x_overlap_index] != assignment[neighbor][y_overlap_index]:
                        return False

            checked.append((var, neighbor))

            # Check for duplicate values
            for var2 in assignment:
                if var == var2:
                    continue
                if assignment[var] == assignment[var2]:
                    return False

        return True

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        
        # DEBUGGING
        # print(f'Var: {var}')
        # print(f'Assignment: {assignment}')
        # self.print_domains()

        # histogram of how many words are taken out of neighboring domains
        # for each domain option in var's domain
        word_rank = {}
        for word in self.domains[var]:
            word_rank[word] = 0

            for neighbor in self.crossword.neighbors(var):
                if neighbor in assignment:
                    continue
                x_overlap_index, y_overlap_index = self.crossword.overlaps[var, neighbor]
                for neighbor_word in self.domains[neighbor]:

                    # remove word from neighbor's domain and 
                    # remove any words from neighbor's domain that conflicts
                    # with the word in var's domain
                    if neighbor_word == word or word[x_overlap_index] != neighbor_word[y_overlap_index]:
                        word_rank[word] += 1

        domain_values = sorted(word_rank.items(), key=lambda x: x[1])

        # DEBUGGING
        # print(f'word_rank for {var}: {word_rank}')
        # print(f'Domain Values for {var}: {domain_values}')

        ordered_domain_values = []
        for word, value in domain_values:
            ordered_domain_values.append(word)

        # DEBUGGING
        # print(f'Ordered Words for {var}: {ordered_domain_values}')

        return ordered_domain_values


    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        # TODO
        # Optimize

        # DEBUGGING
        print(f'Unassigned Variables: ')
        for variable in self.domains:
            if variable not in assignment:
                print(f'    {variable} Domain Length: {len(self.domains[variable])}')

        # Find size of smallest domain
        smallest_domains = []
        smallest_domain_size = float('inf')
        for var in self.crossword.variables:
            if var in assignment:
                continue
            if len(self.domains[var]) == smallest_domain_size:
                smallest_domains.append(var)
            if len(self.domains[var]) < smallest_domain_size:
                smallest_domains = [var]
                smallest_domain_size = len(self.domains[var])

        # If there is only one smallest domain, return that var
        if len(smallest_domains) == 1:
            # DEBUGGING
            print(f'Only one var has smallest domain: {smallest_domains[0]}')
            return smallest_domains[0]

        # Among those tied for smallest domain, find the one with
        # the largest degree of neighbors not already assigned     
        largest_degree = []
        most_neighbors = 0
        for v in smallest_domains:
            unassigned_neighbors = [neighbor
                            for neighbor in self.crossword.neighbors(v)
                            if neighbor not in assignment]
            if len(unassigned_neighbors) == most_neighbors:
                largest_degree.append(v)
            if len(unassigned_neighbors) > most_neighbors:
                largest_degree = [v]
                most_neighbors = len(unassigned_neighbors)
        
        # DEBUGGING
        print(f'Vars with lowest domains and most neighbors: ')
        for ld in largest_degree:
            print(f'    {ld} has a domain of {len(self.domains[ld])}')
            unassigned_neighbors = [neighbor
                            for neighbor in self.crossword.neighbors(ld)
                            if neighbor not in assignment]
            print(f'    and {len(unassigned_neighbors)} unassigned neighbors')
        print(f'')
        print(f'')

        return choice(largest_degree)
            

            
            

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        # TODO
        # Could still optimize by interleaving arc-consistency with the search
        
        if self.assignment_complete(assignment):
            return assignment
  
        var = self.select_unassigned_variable(assignment)
        for value in self.order_domain_values(var, assignment):

            # Add a new variable to assignment  
            assignment[var] = value

            # Create a copy of self.domains as it is,
            # So that after modifying it through the AC-3 algorithm
            # It can be reversed if the result fails
            domains_copy = deepcopy(self.domains)

            # Is the variable consistent? i.e. does it conflict
            if self.consistent(assignment):

                # Update self.domains to reflect current assignment
                # And check for arc consistency with new self.domain and
                # new assigned var
                arcs = []
                for variable in assignment:
                    self.domains[variable] = {assignment[variable]}

                    # DEBUGGING
                    # print(f'self.domains[{variable}] = {assignment[variable]}')

                    for neighbor in self.crossword.neighbors(variable):
                        if neighbor not in assignment:
                            arcs.append((neighbor, variable))

                # DEBUGGING
                # print(f'arcs being passed in: {arcs}')

                if self.ac3(arcs):

                    result = self.backtrack(assignment)
                    if result:
                        return result

            # var didn't work so remove it and try another        
            del assignment[var]
            self.domains = deepcopy(domains_copy)

        return None

    # DEBUGGING
    def print_domains(self):
        """
        Pretty-print domains for debugging purposes
        """
        for var in self.domains:
            print(f'{var}: {self.domains[var]}')


def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
