class ToolValidator:
  # Class to add custom behavior and properties to the tool and tool parameters.

    def __init__(self):
        # set self.params for use in other function
        self.params = arcpy.GetParameterInfo()

    def initializeParameters(self):
        # Customize parameter properties. 
        # This gets called when the tool is opened.
        return

    def updateParameters(self):
        # Modify parameter values and properties.
        # This gets called each time a parameter is modified, before 
        # standard validation.
        
        if not self.params[0].altered:
            self.params[1].enabled = False
        else:
            self.params[1].enabled = True

        if not self.params[1].altered:
            self.params[2].enabled = False
        else:
            self.params[2].enabled = True
    
        if not self.params[2].altered:
            self.params[3].enabled = False
            self.params[4].enabled = False
        else:
            self.params[3].enabled = True
            self.params[4].enabled = True
        
        if not self.params[4].altered:
            self.params[5].enabled = False
            self.params[6].enabled = False
            self.params[7].enabled = False
        else:
            self.params[5].enabled = True
            self.params[6].enabled = True
            self.params[7].enabled = True
        
        return

    def updateMessages(self):
        # Customize messages for the parameters.
        # This gets called after standard validation.
        return

    # def isLicensed(self):
    #     # set tool isLicensed.
    # return True
