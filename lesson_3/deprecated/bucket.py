import numpy as np
import itertools as it

class Bucket():
    
    """
    A class that implements the data structure for the bucket elimination


    Attributes
    ----------
        variable : str
            a string that represent the variable of the bucket (literals)
        soft_cnst : list
            the soft contraints, a list of lists, each list is built with the function name for the first element, 
            followed by the intereseted variables.
        ineq_cnst : list
            the hard contraints (only inequality constraints), a list of lists, 
            each list represent the variable interested in the inequality contraints.
        table : int
            tabular form of the function generated from the bucket constraints
        h_table : int
            tabular form of the h_function generated from the bucket function on the bucket variable

    Methods
    -------
        get_tables( domains, h_functions, h_variables )
            method that compute and return the table and the h_table of the bucket
    """
        
    
    def __init__( self, variable, soft_cnst=[], ineq_cnst=[] ):
        
        """
        Constructor of the class

        Parameters
        ----------
            variable : str
                a string that represent the variable of the bucket (literals)
            soft_cnst : list
                the soft contraints, a list of lists, each list is built with the function name for the first element, 
                followed by the intereseted variables.
            ineq_cnst : list
                the hard contraints (only inequality constraints), a list of lists, 
                each list represent the variable interested in the inequality contraints.
        """
            
        self.variable = variable
        self.soft_cnst = soft_cnst
        self.ineq_cnst = ineq_cnst
        
        self.table = None
        self.h_table = None
      
        
    def get_tables( self, domains, h_functions, h_variables ):
        
        """
        Compute the bucket function and the bucket h_function on the bucket variable. Store the generated function in the
        private variables "self.table" and "self.h_table".

        Parameters
        ----------
            domains : list 
                the domain of the variables, a dictionary with the variable name as key and a list for the discrete domain as a value.
            h_functions : list
                the additional h_function as soft constraints, a list of list, 
                each list is a representation of the h_function in a tabular form
            h_variables : list
                the variables that appear in the h_table (literals of the function), a list of string with the name of the variables.

        Returns:
        --------
            table : list
                the resulting function as table. A list of dictionaries, each dictionary of the list is a row;
                the key is the column value name and is the corresponding value row/column.  
            h_table : list
                the resulting h_function as a h_table. A list of dictionaries, each dictionary of the list is a row;
                the key is the column value name and is the corresponding value row/column.  
            variables : list
                the variables that appear in the table, a list of the given literals merged with the variables of the h_tables,
                ordered and wothout repetition
        """
            
        # Compute the variables list from the constraints and delete duplicate from list  
        cnst_variables = [ cst[1:] for cst in self.soft_cnst] 
        cnst_variables += [ [var for var in cst] for cst in self.ineq_cnst]
        cnst_variables = list(set(sum(cnst_variables, [])))
        
        # Add the variables of the h_functions
        variables = sorted(list(set(cnst_variables + h_variables)))
        
        #
        self.table = self._create_table( variables, domains, self.soft_cnst, h_functions, self.ineq_cnst )
        self.h_table = self._extract_h_function( self.table, self.variable, domains )
        
        #
        return self.table, self.h_table, variables
    
    
    ###################
    # STATIC METHODS  #
    ###################
    
    
    @staticmethod
    def plot_table( table ):
        
        """
        Print the table in a human readable form (static method)

        Parameters
        ----------
            table : list
                list of dictionaries that represent the table, each dictionary of the list is a row. 
                The key is the columns name and is the corresponding value row/column.         
        """

        # Create and print the row for the header
        header_string = ''.join([f" {key:3} |" for key in list(table[0].keys())])
        print( header_string )

        # Create and print the separator
        div_string = ''.join([f"-----|" for key in list(table[0].keys())])
        print( div_string )

        # Create and print each row of the table
        for row in table:
            row_string = ''.join([f" {val:3} |" for val in list(row.values())])
            print(row_string)
        
        
    ###################
    # PRIVATE METHODS #
    ###################
    

    def _create_table( self, variables, problem_domains, soft_const=[], h_functions=[], inequality_const=[] ):

        """
        Create the table of the current bucket with the given parameters

        Parameters
        ----------
            variables : list
                the variables that appear in the table (literals of the function), a list of string with the name of the variables.
            problem_domains : list 
                the domain of the variables, a dictionary with the variable name as key and a list for the discrete domain as a value.
            soft_const : list 
                the soft contraints, a list of lists, each list is built with the function name for the first element, 
                followed by the intereseted variables.
            h_functions : list
                the additional h_function as soft constraints, a list of list, 
                each list is a representation of the h_function in a tabular form
            inequality_const : list
                the hard contraints (only inequality constraints), a list of lists, 
                each list represent the variable interested in the inequality contraints.

        Returns:
        --------
            table : list
                the resulting table as a list of dictionaries. Each dictionary of the list is a row;
                the key is the column value name and is the corresponding value row/column.  

        Raises
        ------
            ValueError
                If the table is empty, no valid solution exists that respects the hard constraints

        """

        # Create a list with all the combinations
        problem_domains_list = [ [d for d in problem_domains[variable]] for variable in variables]    
        combinations = list(it.product(*problem_domains_list))

        # Create the table list of dictionaries
        table = []
        for combo in combinations:
            table.append({})
            for idx, variable in enumerate(variables):
                table[-1][variable] = combo[idx]

        # Evaluate all the soft constraints
        if soft_const != None:
            for idx, const in enumerate(soft_const):
                for row in table:
                    function = const[0]
                    parameters = [row[val] for val in const[1:]]
                    row[f"F_{idx}"] = function(*parameters)

        # Evaluate the additional h_table
        if h_functions != None:
            for idx, h_table in enumerate(h_functions):
                for row in table:
                    h_variables = [var for var in list(h_table[0].keys()) if var in list(problem_domains.keys())]
                    for h_row in h_table:
                        condition_array = [ row[h_variable] == h_row[h_variable] for h_variable in h_variables]
                        if all(condition_array): row[f"h_{idx}"] = h_row["MAX"]

        # Find the rows that violates the inequality constraints
        violated_rows = []
        for const in inequality_const:
            violated_row = []
            for row in table:
                const_value = [row[key] for key in const if key in row.keys()]
                violated_row.append( len(const_value) > 1 and len(set(const_value)) == 1 )
            violated_rows.append(violated_row.copy())

        # Find the violated rows from the h_table used
        violated_row = []
        for idx, row in enumerate(table):
            violated_row.append(False)
            for key in row.keys():     
                if row[key] == -np.inf: 
                    violated_row[-1] = True
                    break
        violated_rows.append(violated_row.copy())

        # Delete the rows that violates the properties
        logical_mask = np.logical_or.reduce(violated_rows)
        table = np.array(table)[np.logical_not(logical_mask)].tolist()
        if len(table) == 0: raise ValueError("No solution that respect all the hard constraints exists")

        # Evaluate the sum
        variable_indexes = [idx for idx, key in enumerate(list(row.keys())) if key in variables]
        for row in table:
            joint_sum = [val for idx, val in enumerate(list(row.values())) if idx not in variable_indexes]
            row["SUM"] = sum(joint_sum)

        #
        return table


    def _extract_h_function( self, table, bucket_var, problem_domains ):

        """
        Extract the h_function from the table, and returning it in a tabular form

        Parameters
        ----------
            variables : list
                the variables name for the problem, a list of string with the name of the variables.
            bucket_var : string 
                the name of the variable of the current bucket. The variable that we use for the maximization
            problem_domains : list 
                the domain of the variables, a dictionary with the variable name as key and a list for the discrete domain as a value.

        Returns:
        --------
            h_table : list
                the resulting h_function (in a tabular form) as a list of dictionaries. Each dictionary of the list is a row;
                the key is the column name and the value is the corresponding value row/column. If the 'MAX' value is -inf it means that 
                the corresponding row is not valid given the inherited hard constraints.
        """

        # Intialize the h_table and extract the variable list of the table (i.e., all the variables of the table except
        # the bucket variable.
        h_table = []        
        checking_variables = [var for var in list(table[0].keys()) if (var in list(problem_domains.keys()) and var != bucket_var )]

        # Get the combinations for this subdomain of variables
        problem_domains_list = [ [d for d in problem_domains[variable]] for variable in checking_variables]    
        combinations = list(it.product(*problem_domains_list))

        # Create the table list of dictionaries (-inf) is the default value
        for combo in combinations:
            h_table.append({})
            for idx, variable in enumerate(checking_variables):
                h_table[-1][variable] = combo[idx]
            h_table[-1]['MAX'] = -np.inf

        # Update the rows of the h_table, extract from the given table the maximum value of all the rows 
        # with the same variables values (except the bucket variable)
        for row in table:
            for h_row in h_table:
                mask_array = [ row[key] == h_row[key] for key in checking_variables]
                if all(mask_array):
                    h_row['MAX'] = max(h_row['MAX'], row['SUM'])

        #
        return h_table
    
    
    def __str__( self ):
        
        """
        Override of the standard to string method

        Returns:
        --------
            to_string : str
                a human readable form for the print method
        """
        
        return f"Bucket of Variable: ({self.variable}). \n\tNumber of soft constraints: {len(self.soft_cnst)} \
                    \n\tNumber of hard constraints: {len(self.ineq_cnst)}"