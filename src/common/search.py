import sys 


records = [{"id": 1, 
           "name": "Alice",
           "City": "Houston"
        },
           {"id": 2, 
           "name": "Bob",
           "City": "Dallas"
           
            }
         ##{"id": 2, "name": "Bob"},
         ##{"id": 3, "name": "Charlie"}
         ]



search = input("Enter a name or ID number to search for: ")

found = False

for record in records:

    searchable_text = "".join(str(value) for value in record.values()).lower()

    if search in searchable_text:
        print(f"Record found: {record}")
        found = True
        break

if not found:
    print(f"{search} not found.")






