import tkinter as tk
import mysql.connector
from tkinter import ttk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageOps
import io

# Create a function to fetch data from the MySQL table and populate the Tkinter Treeview
def fetch_data():
    # Define your MySQL connection parameters
    db_connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="123",
        database="try_schema"
    )

    # Create a cursor object to execute SQL queries
    cursor = db_connection.cursor()

    # Execute an SQL query to select data from your table
    cursor.execute("SELECT * FROM table_1")

    # Fetch all the rows from the result set
    data = cursor.fetchall()

    # Close the cursor and the database connection
    cursor.close()
    db_connection.close()

    # Clear the Treeview
    for item in treeview.get_children():
        treeview.delete(item)

    # Populate the Tkinter Treeview with the data
    for record in data:
        treeview.insert('', 'end', values=record)

# Center the text in each cell of the Treeview
def center_text(event):
    col_width = 100  # Adjust this value as needed
    for col in treeview["columns"]:
        treeview.column(col, width=col_width, anchor="center")

# Function to fetch image data from the MySQL table
def fetch_image_data(selected_item):
    # Retrieve the selected row's data, including the image
    item = treeview.item(selected_item)
    img_id = item["values"][0]  # Assuming the ID is in the first column

    # Define your MySQL connection parameters
    db_connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="123",
        database="try_schema"
    )

    # Create a cursor object to execute SQL queries
    cursor = db_connection.cursor()

    # Execute an SQL query to fetch the image data for the selected row
    cursor.execute("SELECT img FROM table_1 WHERE ID = %s", (img_id,))

    # Fetch the image data
    img_data = cursor.fetchone()[0]

    # Close the cursor and the database connection
    cursor.close()
    db_connection.close()

    return img_data

# Function to display the selected image
def display_selected_image(event):
    selected_item = treeview.selection()
    if selected_item:
        # Fetch the image data from the selected row
        img_data = fetch_image_data(selected_item)

        try:
            # Convert binary image data to an image
            image = Image.open(io.BytesIO(img_data))

            # Resize the image to half the size of the window
            window_width = root.winfo_width()
            window_height = root.winfo_height()
            new_width = window_width // 2
            image = image.resize((new_width - 30, 500), Image.ANTIALIAS)

            photo = ImageTk.PhotoImage(image)

            # Update the image label with the new image
            image_label.config(image=photo)
            image_label.image = photo  # Keep a reference

            # Fetch and display the available quantity below the image
            display_available_quantity(selected_item)
        except Exception as e:
            print(f"Error: {e}")

def display_available_quantity(selected_item):
    item = treeview.item(selected_item)
    available_quantity = item["values"][5]  # Assuming Available is in the sixth column
    available_label.config(text=f"In Stock: {available_quantity}")

def add_item():
    # Retrieve data from the entry widgets
    new_item = item_entry.get()
    new_price = price_entry.get()
    new_quantity = quantity_entry.get()
    
    # Validate that new_price and new_quantity are valid integers
    try:
        new_price = float(new_price)
        new_quantity = int(new_quantity)
    except ValueError:
        messagebox.showinfo("Error", "Price and Quantity must be valid numbers.")
        return

    if not new_item or not new_price or not new_quantity:
        messagebox.showinfo("Error", "Please fill in all item details before adding an image.")
        return

    # Define your MySQL connection parameters
    db_connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="123",
        database="try_schema"
    )

    # Create a cursor object to execute SQL queries
    cursor = db_connection.cursor()

    # Execute an SQL query to select the last added item's ID
    cursor.execute("SELECT ID FROM table_1 ORDER BY ID DESC LIMIT 1")
    last_item = cursor.fetchone()

    if last_item:
        last_item_id = last_item[0]
    else:
        last_item_id = 0

    # Increment the last item's ID to generate the new item's ID
    new_item_id = last_item_id + 1

    # Execute an SQL query to select the item by name
    cursor.execute("SELECT ID, Price, Quantity, Available FROM table_1 WHERE Item = %s", (new_item,))
    existing_item = cursor.fetchone()

    if existing_item:
        item_id, existing_price, existing_quantity, existing_available = existing_item

        # Check if the prices are different
        if float(new_price) != existing_price:
            response = messagebox.askquestion(
                "Price Update",
                f"This item already exists with a different price. Do you want to update the price in the database from Php{existing_price} to Php{new_price}?"
            )
            if response == "yes":
                existing_quantity += int(new_quantity)
                existing_available += int(new_quantity)
                update_query = "UPDATE table_1 SET Price = %s, Quantity = %s, Available = %s WHERE ID = %s"
                cursor.execute(update_query, (new_price, existing_quantity, existing_available, item_id))
                db_connection.commit()
                messagebox.showinfo("Price Updated", "Price updated successfully.")
        else:
            existing_quantity += int(new_quantity)
            existing_available += int(new_quantity)
            update_query = "UPDATE table_1 SET Quantity = %s, Available = %s WHERE ID = %s"
            cursor.execute(update_query, (existing_quantity, existing_available, item_id))
            db_connection.commit()
        
        messagebox.showinfo("Item Updated", "Quantity and availability updated successfully.")
    else:
        # Notify the user to choose a photo
        messagebox.showinfo("Select an Image", "Please choose a photo for the item.")
        
        # Open a file dialog to select an image
        image_path = filedialog.askopenfilename()
        
        if not image_path:
            return  # User canceled image selection

        # Read the selected image
        with open(image_path, 'rb') as image_file:
            img_data = image_file.read()

        # Insert the new item data into the database with the generated new_item_id
        insert_query = "INSERT INTO table_1 (ID, Item, Price, Quantity, Sold, Available, Subtotal, img) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(insert_query, (new_item_id, new_item, new_price, new_quantity, 0, new_quantity, 0, img_data))
        db_connection.commit()

        messagebox.showinfo("Item Added", "Item added successfully.")

    # Close the cursor and the database connection
    cursor.close()
    db_connection.close()

    # Update the Treeview with the new data
    fetch_data()

    # Clear the entry fields
    item_entry.delete(0, tk.END)
    price_entry.delete(0, tk.END)
    quantity_entry.delete(0, tk.END)

def delete_item():
    selected_item = treeview.selection()
    if selected_item:
        item = treeview.item(selected_item)
        item_id = item["values"][0]  # Assuming the ID is in the first column

        # Ask the user for confirmation
        confirmation = messagebox.askokcancel("Confirm Deletion", "Are you sure you want to delete this item?")

        if confirmation:
            # Define your MySQL connection parameters
            db_connection = mysql.connector.connect(
                host="localhost",
                user="root",
                password="123",
                database="try_schema"
            )

            # Create a cursor object to execute SQL queries
            cursor = db_connection.cursor()

            # Execute an SQL query to delete the item from the database
            cursor.execute("DELETE FROM table_1 WHERE ID = %s", (item_id,))
            db_connection.commit()

            # Close the cursor and the database connection
            cursor.close()
            db_connection.close()

            # Delete the selected item from the Treeview
            treeview.delete(selected_item)
            messagebox.showinfo("Item Deleted", "Item deleted successfully.")
        else:
            return

def update_delete_button_state(event):
    # Check if any row is selected
    selected_item = treeview.selection()
    if selected_item:
        delete_button.config(state="normal")
    else:
        delete_button.config(state="disabled")

root = tk.Tk()
root.title("Acer Laptop Inventory Sales")
root.geometry("1500x720")
root.geometry("+10+30")

# Create a Canvas widget for the background image
canvas = tk.Canvas(root, width=1500, height=720)
canvas.pack()
background_image = Image.open("C:/Users/danil/OneDrive/Desktop/JR/_ElectiveProject/Laptop Images/bg.png")
background_image = ImageOps.fit(background_image, (1500, 720), Image.Resampling.LANCZOS)
background_photo = ImageTk.PhotoImage(background_image)
canvas.create_image(0, 0, anchor=tk.NW, image=background_photo)

# Create a frame to contain all components on the canvas
table_frame = tk.Frame(canvas)  # Remove the fixed height
canvas.create_window(20, 20, window=table_frame, anchor=tk.NW)

# Create a Treeview widget to display the data within the frame
treeview = ttk.Treeview(table_frame, columns=("ID", "Item", "Price", "Quantity", "Sold", "Available", "Subtotal"), height=24)
treeview.heading("ID", text="ID")
treeview.heading("Item", text="Item")
treeview.heading("Price", text="Price")
treeview.heading("Quantity", text="Quantity")
treeview.heading("Sold", text="Sold")
treeview.heading("Available", text="Available")
treeview.heading("Subtotal", text="Subtotal")
treeview.pack(fill="both", expand=True)  # Allow the Treeview to fill the available space

# Call fetch_data to populate the Treeview upon window boot
fetch_data()

# Configure column weights to make them fill the available space
treeview.column("#0", width=0, stretch=tk.NO)  # Hide the leftmost empty column
for col in treeview["columns"]:
    treeview.column(col, width=100, stretch=tk.YES)
    treeview.heading(col, text=col)

# Bind an event to center the text
treeview.bind("<Configure>", center_text)

# Bind TreeviewSelect event to display selected image
treeview.bind("<<TreeviewSelect>>", display_selected_image)

# Create a label for image preview on the right side
image_label = tk.Label(canvas)
canvas.create_window(755, 20, window=image_label, anchor=tk.NW)

# Create a label to display available quantity above the image
available_label = tk.Label(canvas, text="", font=("Arial", 25, "bold"))
canvas.create_window(1050, 540, window=available_label, anchor=tk.NW)

# Create entry widgets for new item details
add_block = tk.Label(root, background="black", width=41, height=11)
add_block.place(x=20, y=530)

sale_block = tk.Label(root, background="black", width=41, height=11)
sale_block.place(x=320 , y=530)

add_block2 = tk.Label(root, background="grey", width=39, height=10)
add_block2.place(x=20, y=530)

sale_block2 = tk.Label(root, background="grey", width=39, height=10)
sale_block2.place(x=320 , y=530)

item_label = tk.Label(root, text="Item:", bg = 'grey')
item_label.place(x=50, y=570)
item_entry = tk.Entry(root)
item_entry.place(x=150, y=570)

price_label = tk.Label(root, text="Price:", bg = 'grey')
price_label.place(x=50, y=590)
price_entry = tk.Entry(root)
price_entry.place(x=150, y=590)

quantity_label = tk.Label(root, text="Quantity:", bg = 'grey')
quantity_label.place(x=50, y=610)
quantity_entry = tk.Entry(root)
quantity_entry.place(x=150, y=610)

main_label = tk.Label(root, text="ADD ITEMS IN THE INVENTORY", bg = 'grey', fg="green", font=("Arial", 13, "bold"))
main_label.place(x=35, y=535)

main_label2 = tk.Label(root, text="ADD SALES", bg = 'grey', fg="green", font=("Arial", 13, "bold"))
main_label2.place(x=415, y=535)

# Create an "ADD" button
add_button = tk.Button(root, text="ADD", command=add_item, width=20, height= 2)
add_button.place(x=90, y=640)

# Create the delete button
delete_button = tk.Button(root, text="DELETE", foreground="red", command=delete_item, width=13, height=2, state="disabled")
delete_button.place(x=620, y=530)

# Create a Search button
item_entry2 = tk.Entry(root)
item_entry2.place(x=400, y=560)

search_button = tk.Button(root, text="Search", width=10, height=1)
search_button.place(x=423, y=585)

# Bind the ButtonRelease-1 event to update the delete button state
treeview.bind("<ButtonRelease-1>", update_delete_button_state)

# Lock the window size
root.resizable(width=False, height=False)

root.mainloop()
