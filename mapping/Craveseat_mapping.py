from graphviz import Digraph
from IPython.display import Image




# Initialize directed graph
erd = Digraph(format="png")
erd.attr(rankdir="LR", size="8")

# Define tables as nodes
erd.node("Users", """Users
-----------------
id (PK)
username (unique)
email (unique)
password_hash
full_name
bio
profile_image_url
is_vendor (bool)
created_at
updated_at""")

erd.node("Cravings", """Cravings
-----------------
id (PK)
user_id (FK)
title
description
category
status (enum)
anonymous (bool)
created_at
updated_at""")

erd.node("Responses", """Responses
-----------------
id (PK)
craving_id (FK)
user_id (FK)
message
status (enum)
created_at""")

erd.node("Vendors", """Vendors (optional)
-----------------
id (PK)
user_id (FK)
business_name
location
service_category
rating""")

# Define relationships
erd.edge("Users", "Cravings", label="1..*")
erd.edge("Users", "Responses", label="1..*")
erd.edge("Cravings", "Responses", label="1..*")
erd.edge("Users", "Vendors", label="1..1 (if vendor)")

# Render ERD
erd.render("C:\Users\USER\Desktop\Craveseat_erd", view=True)
"C:\Users\USER\Desktop\Craveseat_erd.png"

Image(erd.render(format="png"))