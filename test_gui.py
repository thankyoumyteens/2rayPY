import tkinter as tk


def change_node():
    node_name = node_name_input.get()
    print(node_name)


window = tk.Tk()

window.title('V2ray py')
width = 800
height = 600
screenwidth = window.winfo_screenwidth()
screenheight = window.winfo_screenheight()
rect = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
window.geometry(rect)
window.resizable(width=False, height=False)

tk.Label(window, text="node name").grid(row=0)
node_name_input = tk.Entry(window)
node_name_input.grid(row=0, column=1)

tk.Button(window, text='use', command=change_node).grid(row=0, column=2, padx=5, pady=5)

tk.Button(window, text='update', command=change_node).grid(row=1, column=0, padx=5, pady=5)
tk.Button(window, text='ping all', command=change_node).grid(row=1, column=1, padx=5, pady=5)

sb = tk.Scrollbar(window)
sb.grid(sticky=tk.E+tk.N+tk.S, column=1)
node_list_box = tk.Listbox(window, yscrollcommand=sb.set)
node_list_box.grid(row=2, column=0, padx=5, pady=5)
node_list_box.insert(tk.END, 'aaa')
sb.config(command=node_list_box.yview)

window.mainloop()
