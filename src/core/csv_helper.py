# https://stackoverflow.com/a/51688035/12637568

NULLS = {'NULL', 'null', 'None', ''}

def cleaned_rows(reader):
    def clean(row: list[str]) -> None | str:
        for cell in row:
            cell = cell.strip()
            
            if cell in NULLS:
                yield None
            else:
                yield cell

    for row in reader:
        yield clean(row)