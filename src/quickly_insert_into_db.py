import sqlite3
import csv
from operator import itemgetter
from pprint import pprint

# enter csv data into the db

ENABLE_SQL = True
CSV_FILEPATH = r"C:\Users\z\Desktop\planetary\Planetary-HTML-Table-generator\src\planet_data.csv"
DB_FILEPATH = r"C:\Users\z\Desktop\planetary\Planetary-HTML-Table-generator\src\planet_data.db"

if ENABLE_SQL:
    con = sqlite3.connect(DB_FILEPATH)
    cur = con.cursor()

with open(CSV_FILEPATH, 'r') as file_object:
    # Strip trailing spaces after deliminators (trailing spaces are used for visual appeal):
    # Permit commas with trailing spaces within quoted cells:
    # https://stackoverflow.com/questions/8311900/read-csv-file-with-comma-within-fields-in-python
    # If we need to perform numeric calculation, quoting=csv.QUOTE_NONNUMERIC will come in handy.
    csv_reader = csv.DictReader(file_object, skipinitialspace=True)
    
    for row_dict in csv_reader:
        planet_type = row_dict["type"]
        planet_subtype = row_dict.get("subtype")
        
        data = { **row_dict }
        del data["type"]
        del data["subtype"]
        
        data.setdefault("notes", data.get("notes", None))
        
        if ENABLE_SQL:
            planet_seq_current = cur.execute("""
                SELECT "seq" + 1
                FROM "sqlite_sequence"
                WHERE "name" = 'planet';
            """).fetchone()[0]
            
            cur.execute("""
                UPDATE "sqlite_sequence"
                SET "seq" = "seq" + 1
                WHERE "sqlite_sequence"."name" = 'planet';
            """)
            con.commit()

            # Choose the subheader if available, otherwise the header.
            # why are these variables not hoisted outside of the if statement?
            # my old django code had some hoisting if I recall.. look into it
            planet_final_type = planet_subtype if planet_subtype else planet_type
            planet_header_id = cur.execute("""
                SELECT header_id
                FROM main.header
                WHERE name = ?;
            """, (planet_final_type,)).fetchone()[0]
            
            data["planet_id"] = planet_seq_current
            data["header_id"] = planet_header_id
        
        if ENABLE_SQL:
            print(f"inserted id#{planet_seq_current} into planet")
            cur.execute("""
                INSERT INTO planet
                VALUES
                    (:planet_id,:name,:mass,:diameter,:density,
                     :gravity,:day_length,:dist_from_sun,:avg_temp,
                     :moon_count,:header_id,:notes);
            """, data)
            con.commit()
        
if ENABLE_SQL:   
    con.close()
    
print("\nSuccess")