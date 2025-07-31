import os
import warnings
import csv
import sqlite3
from operator import itemgetter
from typing import Self, Any

############
# Settings #
############

DEBUG = False

INPUT_DB_FILENAME = "planet_data.db"
OUTPUT_DIR = "public"

# It's best not to touch these #

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
INPUT_DB_PATH = os.path.join(BASE_DIR, INPUT_DB_FILENAME)

ROOT_DIR = os.path.join(BASE_DIR, "..")
OUTPUT_PATH = os.path.join(ROOT_DIR, OUTPUT_DIR)

WELCOME_MESSAGE = """
#################################
    Planetary HTML Table Generator
#################################
"""

############

class TemplateNotFoundException(Exception):
    pass


class Template:
    """A static HTML page with dynamic data insertion capability."""
    
    # Python's __init__ return type is controversial.
    def __init__(self, template_path: str) -> None:
        self.template_path: str = template_path
        
        self.fullname: str = os.path.basename(template_path)

    def get_contents(self) -> str:
        """Return the HTML contents of a template file as a string."""
        with open(self.template_path, 'r') as file_object:
            return file_object.read()

    def render(self, context_data: dict[str, str]) -> str:
        """Populate a template's unfilled format variables with context data."""
        html_contents = self.get_contents()
        
        return html_contents.format(**context_data)

    # If we create subclasses from this Template,
    # ... we may need a get_template() mixin to properly annotate
    # ... the cls type as Template.
    @classmethod
    def get_template(cls: Self, template_name: str) -> Self:
        """Return a template class created via the passed template name.
        Recursively searches the /src/templates/ dir until the first occurence of
        <template_name>.html is found. Will raise an error if nothing is found."""
        
        template_file_name = f"{template_name}.html"
        
        for root, dirs, files in os.walk(TEMPLATES_DIR):
            if template_file_name in files:
                return cls(os.path.join(root, template_file_name))
        
        raise TemplateNotFoundException(f"Could not find template {template_name} in src/templates/")


def minify(html_contents: str) -> str:
    """Remove whitespace and newlines from the HTML."""
    warnings.warn("Minification is yet to be implemented.")
    
    return html_contents


def format_document(html_contents: str) -> str:
    """Format an HTML document via Prettier."""
    warnings.warn("Formatting is yet to be implemented.")
    
    return html_contents


def generateTableBodyFromDB(db_filepath: str) -> str:
    """Produce a string of <th> and <td> tags from the DB file.
    
        Expects the data input file to positionally contain:
            string, 8 floats, optional string
        
        Data Input:
            Mercury 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 [optional: Space-separated words]
        Data Output:
            <th>Mercury</th><td>0.0</td> ... <td>A string of words</td>
    """
    tbody_contents: str = ""
    
    with sqlite3.connect(db_filepath) as connection:
        tr_headers_created = {}
        
        for planet_record in connection.execute("SELECT * FROM planet;"):
            planet_name = planet_record[1]
            planet_data_floats = planet_record[2:-2]
            planet_submost_header_id = planet_record[-2]
            planet_notes = planet_record[-1]
            
            # we'll create our ordering for the list above starting at 0
            # for the subchild, then counting up to the parent (it's easier)
            
            # once i git gud at sql, I could implement the reverse order which makes
            # more sense. I'd need to count the number of headers in the chain from
            # any point in the chain to be able to correctly add an order index
            # to the subchildren, since I'll be starting from the subchild.
            
            # also to learn:
            # pro git!! sql joins, anti-joins, create my own db business kingdom,
            # sql selection, ddl, all the d*ls, nelson's course, pgwiki,
            # HTML, CSS, JS, lots of sql practice, linux bash scripts via fcc
            # sql book. just lots of hard consistent work.
            
            # retrieve the number of rows that share this record's header.
            # the header will always be the lowest in the subheader hierarchy.
            # if a parent_id exists, walk up the chain and assign to variables
            # such that it allows reconstruction in the HTML.
            
            headers_to_create: list[dict] = [
                # (0, "Child'sChild2", 1),
                # (1, "Child'sChild", 1),
                # (2, "Child'sChild", 1),
                # (3, "Child", 3),
                # (4, "Parent", 3), ???????????/ how to get rowspan 3.... hmmm...
                # algorithm to add up subchildren? sql query to calculate it for us?......
            ]
            
            # general tree traversal
            # How do we write the correct row headers & rowspans
            # for the HTML table?
            # How do we write these headers first, once?
                # flags - headers_to_create
                # write once, write any submost rows, remove subheader, write next subheader
                
                # select rows of this subheader
                # write them
                # do the next subheader
            
            # Possible limitations that require: #
            #   CTEs, Subqueries, Recursive Queries, Unions,
            #   Functions, Triggers
            
            # All planets in the DB refer only to submost headers. #
            
            planet_submost_header_name = connection.execute("""
                SELECT "header"."name"
                FROM "header"
                WHERE "sub_header"."header_id" = ?;
            """, (planet_submost_header_id,)).fetchone()
            
            rows_of_same_submost_header: list[Any] = connection.execute(
                "SELECT COUNT(*) FROM planet GROUP BY header_id HAVING header_id = ?",
                (planet_submost_header_id,)
            ).fetchone()
            
            headers_to_create.append(
                {
                    "creation_reverse_index": 0,
                    "header_name": planet_submost_header_name[0],
                    "planets_pointing_to_header": rows_of_same_super_header[0],
                    "headers_pointing_to_header": 0,
                }
            )
            
            # index, header name, rowspan
            # index: order the submost header (index of 0) in the parent-child hierarchy
            #        ... to the topmost parent header (largest index value)
            # rowspan: number of rows that the header spans. used to
            #        ... reconstruct the heading into HTML table row headings
            next_super_header: tuple[int, str]
    
            # Continue to iterate until no more headers exist
            # .. in the chain.
            while next_super_header:
                # grab next super header id & name
                next_super_header = connection.execute("""
                    SELECT "super_header"."header_id", "super_header"."name"
                    FROM "header" as "super_header"

                    INNER JOIN "header" as "sub_header"
                    ON "super_header"."header_id" = "sub_header"."parent_id"

                    WHERE "sub_header"."header_id" = ?;
                """, (next_super_header[0] or planet_submost_header_id,)).fetchone()
                
                # If a parent header exists for the current subheader...
                if next_super_header:
                    rows_of_same_super_header: list[Any] = connection.execute(
                        "SELECT COUNT(*) FROM planet GROUP BY header_id HAVING header_id = ?",
                        (next_super_header[0],)
                    ).fetchone()
                    
                    # sql navigate to the root of a tree from any point
                    # sql find how many leafs exist from the top of a tree
                    
                    # SELECT COUNT(*) FROM header WHERE header_id NOT EXISTS IN (SELECT)
                    leafs_of_root = connection.execute("" \
                    "" \
                    "")
                    
                    # traverse downwards to find all headers that point to this one...
                    rows_of_same_super_header: list[Any] = connection.execute("""
                        SELECT COUNT(*)
                        FROM header
INNER JOIN "headers" 


                    """, (next_super_header[0],)
                    ).fetchone()
                    
                    headers_to_create.append(
                        {
                            "creation_reverse_index": len(headers_to_create),
                            "header_name": next_super_header[1],
                            "planets_pointing_to_header": rows_of_same_super_header[0],
                            "headers_pointing_to_header": 0,
                        }
                    )
                else:
                    
                    
            # Better suited as a DB query
            # rows_of_type = 
            # ... logic to calculate rowspan and colspans ...
            
            # Write to HTML partial buffer
            tbody_contents += ("<tr>\n")
            
            # huh.....
            if planet_submost_header not in tr_headers_created:
                # Topmost super header reached. Write the row:
                if not next_super_header:
                    tbody_contents += f"<th rowspan=\"{len(tr_headers_created)}\">{planet_submost_header}</th>\n"
            #############
            
            tbody_contents += f"<th>{planet_name}</th>\n"
            for datum in planet_data_floats:
                tbody_contents += f"<td>{datum}</td>\n"
            
            if planet_notes != '':
                tbody_contents += f"<td>{planet_notes}</td>\n"
                
            tbody_contents += "</tr>\n"
    
    if not tbody_contents:
        raise Exception("No data present in file supplied.")
    
    return tbody_contents




def generateTableBody(csv_filepath: str) -> str:
    """Produce a string of <th> and <td> tags from the passed csv file.
    
        Expects the data input file to positionally contain:
            string, 8 floats, optional string
        
        Data Input:
            Mercury 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 [optional: Space-separated words]
        Data Output:
            <th>Mercury</th><td>0.0</td> ... <td>A string of words</td>
    """
    tbody_contents: str = ""
    
    with open(csv_filepath, 'r') as file_object:
        # Strip trailing spaces after deliminators (trailing spaces are used for visual appeal):
        # Permit commas with trailing spaces within quoted cells:
        # https://stackoverflow.com/questions/8311900/read-csv-file-with-comma-within-fields-in-python
        # If we need to perform numeric calculation, quoting=csv.QUOTE_NONNUMERIC will come in handy.
        csv_reader = csv.DictReader(file_object, skipinitialspace=True)
        
        # make it super dynamic
        # count # of types/subtypes
        # create rowspans and colspans based on row count and subtype count of parent
        # yuhhh
        # getting griddy here
        
        for row_dict in csv_reader:
            planet_name = row_dict["Name"]
            planet_type = row_dict["Type"]
            planet_subtype = row_dict.get("Subtype")
            floats = itemgetter(
                "Mass", "Diameter", "Density", "Gravity",
                "Day Length", "Distance from Sun",
                "Average Temperature", "Moon Count"
            )(row_dict)
            comment = row_dict.get("Notes")
            
            # Better suited as a DB query
            # rows_of_type = 
            
            # Write to HTML partial buffer
            tbody_contents += ("<tr>\n")
            
            tbody_contents += f"<th>{planet_name}</th>\n"
            for datum in floats:
                tbody_contents += f"<td>{datum}</td>\n"
            
            if comment:
                tbody_contents += f"<td>{comment}</td>\n"
                
            tbody_contents += "</tr>\n"
    
    if not tbody_contents:
        raise Exception("No data present in file supplied.")
    
    return tbody_contents


def publish_tabular_data() -> None:
    """Generate, render, and write planetary data
    to an HTML file under /public/."""
    
    table_body: str = generateTableBodyFromDB(INPUT_DB_PATH)

    return 

    context = {
        "table_body": table_body
    }
    
    template: Template = Template.get_template("data_visualized")
    rendered_html: str = template.render(context)
    
    if DEBUG:
        # Apply pretty formatting
        rendered_html = format_document(rendered_html)
    else:
        rendered_html = minify(rendered_html)
    
    output_filepath: str = os.path.join(OUTPUT_PATH, template.fullname)
    with open(output_filepath, "w") as file_object:
        file_object.write(rendered_html)
        

if __name__ == "__main__":
    print(WELCOME_MESSAGE)
    print("Publishing to /public/...\n")
    
    publish_tabular_data() 

    print("\nFinished.")