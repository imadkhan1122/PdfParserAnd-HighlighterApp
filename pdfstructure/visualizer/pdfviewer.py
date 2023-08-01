# importing everything from tkinter
from tkinter import *
from PIL import ImageTk, Image
# importing ttk for styling widgets from tkinter
from tkinter import ttk, PhotoImage
# importing filedialog from tkinter
from tkinter import filedialog as fd
# importing os module
import os
# importing the PDFMiner class from the miner file
from pdfstructure.visualizer.miner import PDFMiner
from pdfstructure.hierarchy.parser import HierarchyParser
from pdfstructure.hierarchy.detectheader import DetectHeaderKID
from pdfstructure.source import FileSource
from pdfstructure.printer import PrettyStringPrinter, JsonStringPrinter, JsonFilePrinter
from pathlib import Path
from pdfstructure.hierarchy.traversal import get_elements_by_page
import csv




# creating a class called PDFViewer
class PDFViewer:
    # initializing the __init__ / special method
    def __init__(self, master):
        # path for the pdf doc
        self.path = None
        # state of the pdf doc, open or closed
        self.fileisopen = None
        # author of the pdf doc
        self.author = None
        # name for the pdf doc
        self.name = None
        # the current page for the pdf
        self.current_page = 0
        # total number of pages for the pdf doc
        self.numPages = None
        
# =============================================================================
#         # creating the window
# =============================================================================
        self.master = master
        # gives title to the main window
        self.master.title('PDF Viewer')
        # gives dimensions to main window
        self.master.geometry('580x520+440+180')
        # this disables the minimize/maximize button on the main window
        self.master.resizable(width = 0, height = 0)
        # loads the icon and adds it to the main window
        
        # img = ImageTk.PhotoImage(Image.open('icons/pdf_icon.png'))
        # icon = PhotoImage(file='icons/pdf_icon.png')
        # self.master.iconphoto(True, icon)
# =============================================================================
#       # creating the menu
# =============================================================================
        self.menu = Menu(self.master)
        # adding it to the main window
        self.master.config(menu=self.menu)
        # creating a sub menu
        self.filemenu = Menu(self.menu)
        # giving the sub menu a label
        self.menu.add_cascade(label="File", menu=self.filemenu)
        
# =============================================================================
#         # adding a two buttons to the sub menus
# =============================================================================
        self.filemenu.add_command(label="Open File", command=self.open_file)
        self.filemenu.add_command(label="Exit", command=self.master.destroy)
        
        
# =============================================================================
#       # Creating top and bottom frames
# =============================================================================
        # creating the top frame
        self.top_frame = ttk.Frame(self.master, width=580, height=460)
        # placing the frame using inside main window using grid()
        self.top_frame.grid(row=0, column=0)
        # the frame will not propagate
        self.top_frame.grid_propagate(False)
        # creating the bottom frame
        self.bottom_frame = ttk.Frame(self.master, width=580, height=50)
        # placing the frame using inside main window using grid()
        self.bottom_frame.grid(row=1, column=0)
        # the frame will not propagate
        self.bottom_frame.grid_propagate(False)
        
# =============================================================================
#       # creating a vertical and horizental scrollbars
# =============================================================================
        # creating a vertical scrollbar
        self.scrolly = Scrollbar(self.top_frame, orient=VERTICAL)
        # adding the scrollbar
        self.scrolly.grid(row=0, column=1, sticky=(N,S))
        # creating a horizontal scrollbar
        self.scrollx = Scrollbar(self.top_frame, orient=HORIZONTAL)
        # adding the scrollbar
        self.scrollx.grid(row=1, column=0, sticky=(W, E))
        
# =============================================================================
#       # Adding the Canvas to the Top Frame and Configuring Its Scrollbars
# =============================================================================
        # creating the canvas for display the PDF pages
        self.output = Canvas(self.top_frame, bg='#ECE8F3', width=560, height=435)
        # inserting both vertical and horizontal scrollbars to the canvas
        self.output.configure(yscrollcommand=self.scrolly.set, xscrollcommand=self.scrollx.set)
        # adding the canvas
        self.output.grid(row=0, column=0)
        # configuring the horizontal scrollbar to the canvas
        self.scrolly.configure(command=self.output.yview)
        
# =============================================================================
#       # Adding The Up, Down Buttons and the Label to the Bottom Frame  
# =============================================================================
        # configuring the vertical scrollbar to the canvas
        self.scrollx.configure(command=self.output.xview)
        # loading the button icons
        # self.uparrow_icon = ImageTk.PhotoImage(file='icons/uparrow.png')
        # self.downarrow_icon = ImageTk.PhotoImage(file='icons/downarrow.png')
        
        # # resizing the icons to fit on buttons
        # self.uparrow = self.uparrow_icon.subsample(3, 3)
        # self.downarrow = self.downarrow_icon.subsample(3, 3)
        # creating an up button with an icon
        self.upbutton = ttk.Button(self.bottom_frame, text="Previous", command=self.previous_page)
        # adding the button
        self.upbutton.grid(row=0, column=1, padx=(270, 5), pady=8)
        # creating a down button with an icon
        self.downbutton = ttk.Button(self.bottom_frame, text="Next", command=self.next_page)
        # adding the button
        self.downbutton.grid(row=0, column=3, pady=8)
        # label for displaying page numbers
        self.page_label = ttk.Label(self.bottom_frame, text='page')
        # adding the label
        self.page_label.grid(row=0, column=4, padx=5)
        self.images = []
        
    # function for opening pdf files
    def open_file(self):
        # open the file dialog
        filepath = fd.askopenfilename(title='Select a PDF file', initialdir=os.getcwd(), filetypes=(('PDF', '*.pdf'), ))
        # checking if the file exists
        if filepath:
            # declaring the path
            self.path = filepath
            # extracting the pdf file from the path
            filename = os.path.basename(self.path)
            # passing the path to PDFMiner 
            self.miner = PDFMiner(self.path)
            # getting data and numPages
            data, numPages = self.miner.get_metadata()
            # setting the current page to 0
            self.current_page = 0
            # checking if numPages exists
            if numPages:
                # getting the title
                self.name = data.get('title', filename[:-4])
                # getting the author
                self.author = data.get('author', None)
                self.numPages = numPages
                # setting fileopen to True
                self.fileisopen = True
                # calling the display_page() function
                self.display_page()
                # replacing the window title with the PDF document name
                self.master.title(self.name)
                
    def get_pdf_data(self, pth):
        #source instance
        doc = FileSource(pth, detectheadercls=DetectHeaderKID)
        doc.load()

        #parser instance
        parser = HierarchyParser(header_conditions_cls=DetectHeaderKID)

        #structure the doc
        output = parser.structure_document(doc)

        return output
    
    # Define a function to make the transparent rectangle
    def create_rectangle(self, x1, y1, x2, y2, **kwargs):
        if 'alpha' in kwargs:
            alpha = int(kwargs.pop('alpha') * 255)
            fill = kwargs.pop('fill')
            fill = self.master.winfo_rgb(fill) + (alpha,)
            image = Image.new('RGBA', (x2-x1, y2-y1), fill)
            self.images.append(ImageTk.PhotoImage(image))
            self.output.create_image(x1, y1, image=self.images[-1], anchor='nw')
        self.output.create_rectangle(x1, y1, x2, y2, **kwargs)

    
    # the function to display the page  
    def display_page(self):
        # checking if numPages is less than current_page and if current_page is less than
        # or equal to 0
        if 0 <= self.current_page < self.numPages:
            # getting the page using get_page() function from miner
            self.img_file = self.miner.get_page(self.current_page)
            # inserting the page image inside the Canvas
            self.output.create_image(0, 0, anchor='nw', image=self.img_file)
            page_ele = get_elements_by_page(self.get_pdf_data(self.path), self.current_page)['elements']
            hdr = ['text', 'label']
            with open('output.csv', 'a') as file:
                csv_writer = csv.writer(file)
                
                csv_writer.writerow(hdr)
                for ele in page_ele:
                    if ele['label'] == 'heading':
                        csv_writer.writerow([ele['text'], 1])
                    else:
                        csv_writer.writerow([ele['text'], 0])
                    
                    if ele['level'] == 1 and ele['label'] == 'heading':
                        bbox = ele['style']['bbox']
                        self.create_rectangle(round(bbox[0]), round(bbox[1]), round(bbox[2]), round(bbox[3]), fill= "#00008B", alpha=0.5)
                    elif ele['level'] == 2 and ele['label'] == 'heading':
                        bbox = ele['style']['bbox']
                        self.create_rectangle(round(bbox[0]), round(bbox[1]), round(bbox[2]), round(bbox[3]), fill= "#FFA500", alpha=0.5)
                    elif ele['level'] == 3 and ele['label'] == 'heading':
                        bbox = ele['style']['bbox']
                        self.create_rectangle(round(bbox[0]), round(bbox[1]), round(bbox[2]), round(bbox[3]), fill= "#FF0000", alpha=0.5)
                    elif ele['level'] == 4 and ele['label'] == 'heading':
                        bbox = ele['style']['bbox']
                        self.create_rectangle(round(bbox[0]), round(bbox[1]), round(bbox[2]), round(bbox[3]), fill= "#800080", alpha=0.5)
                    elif ele['level'] == 5 and ele['label'] == 'heading':
                        bbox = ele['style']['bbox']
                        self.create_rectangle(round(bbox[0]), round(bbox[1]), round(bbox[2]), round(bbox[3]), fill= "#808000", alpha=0.5)
                
            # the variable to be stringified
            self.stringified_current_page = self.current_page + 1
            # updating the page label with number of pages 
            self.page_label['text'] = str(self.stringified_current_page) + ' of ' + str(self.numPages)
            # creating a region for inserting the page inside the Canvas
            region = self.output.bbox(ALL)
            # making the region to be scrollable
            self.output.configure(scrollregion=region)         

    # function for displaying next page
    def next_page(self):
        # checking if file is open
        if self.fileisopen:
            # checking if current_page is less than or equal to numPages-1
            if self.current_page <= self.numPages - 1:
                # updating the page with value 1
                self.current_page += 1
                # displaying the new page
                self.display_page()
                            
    # function for displaying the previous page        
    def previous_page(self):
        # checking if fileisopen
        if self.fileisopen:
            # checking if current_page is greater than 0
            if self.current_page > 0:
                # decrementing the current_page by 1
                self.current_page -= 1
                # displaying the previous page
                self.display_page()



def Visualize():        
    # creating the root window using Tk() class
    root = Tk()
    # instantiating/creating object app for class PDFViewer
    app = PDFViewer(root)
    # calling the mainloop to run the app infinitely until user closes it
    root.mainloop()