from re import findall as regex


def IsNumeric(string):
    for char in string:
        if char not in '0123456789':
            return False
        
    return True


def CheckArray(array):
    output = []
    
    for value in array:
        output.append(True) if value == 'TRUE'                  \
            else output.append(False) if value == 'FALSE'       \
            else output.append(int(value)) if IsNumeric(value)  \
            else output.append(value)
            
    return output


class SetFile(object):
    
    def __init__(self, filename):
        self.items = {}
        
        try:
            with open(filename, 'r', encoding='utf8', errors='strict') as setfile:
                self.data = setfile.readlines()
                
        except Exception as ex:
            self.data = None
            raise Exception(ex)
        
    def parse(self):
        if self.data is not None:
            for line in self.data:
                if not line.startswith('//'):
                    
                    variables = regex(r'(.*) \= (.*)\n', line)
                    for variable in variables:
                        value = f'{variable[1]}'
                        
                        if variable[1] == 'TRUE':
                            value = True
                        elif variable[1] == 'FALSE':
                            value = False
                        elif IsNumeric(variable[1]):
                            value = int(variable[1])
                            
                        self.items.update({f'{variable[0]}': value})
                        
                    arrays = regex(r'(.*) \=\> \[(.*)\]\n', line)
                    for array in arrays:
                        self.items.update({f'{array[0]}': CheckArray(array[1].split(', '))})
