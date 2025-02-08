class Section:
    def __init__(self, name: str):
        self.name = name
    
    def __repr__(self):
        return f"Section('{self.name}')"


class Shelf:
    def __init__(self, height: float, sections: list[str]):
        self.height = height
        self.sections = [Section(name) for name in sections]
    
    def __repr__(self):
        return f"Shelf(height={self.height}, sections={self.sections})"


class Regal:
    def __init__(self,name):
        self.shelves = []
        self.name = name
    
    def add_shelf(self, shelf: Shelf):
        self.shelves.append(shelf)
    
    def find_item(self, item_name: str):
        for shelf_index, shelf in enumerate(self.shelves):
            for section_index, section in enumerate(shelf.sections):
                if section.name == item_name:
                    # return f"Item '{item_name}' found at Shelf {shelf_index + 1}, Section {section_index + 1}"
                    return {"item_name":item_name,
                            "regal_name":self.name,
                            "shelf_index":shelf_index+1,
                            "section_index":section_index+1
                            }
        return None
    
    def get_coordinates(self, item):
        shelf_number = item['shelf_index']
        section_number = item['section_index']
        if shelf_number < 1 or shelf_number > len(self.shelves):
            return "Invalid shelf number"
        shelf = self.shelves[shelf_number - 1]
        
        if section_number < 1 or section_number > len(shelf.sections):
            return "Invalid section number"
        
        section_width = 100 / len(shelf.sections)
        x = (section_number - 1) * section_width + (section_width / 2)
        
        y = sum(self.shelves[i].height for i in range(shelf_number))
        y = y - self.shelves[shelf_number-1].height + 15
        return {"x":round(x),
                "y":round(y)}
    
    def __repr__(self):
        return f"Regal(shelves={self.shelves})"

