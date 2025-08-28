
from marshmallow import ValidationError

class StrongPasswordValidator:
    def __call__(self, password):
        """
        Handles the password validation logic separate from the app class.


        """

        # create a list containing error msg strings
        error_msg_list = []

        # for each found issue, append error msg to list
        if len(password) > 30 or len(password) < 8:
            error_msg_list.append("Error: Password must be between 8 and 30 characters long.")

        specChars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        longEnough, upperBoolean, lowerBoolean, containsNum, containsSpec = False, False, False, False, False
        for char in password:
            if char.isupper():
                upperBoolean = True
            if char.islower():
                lowerBoolean = True
            if char.isdigit():
                containsNum = True
            if char in specChars:
                containsSpec = True

        if not upperBoolean:
            error_msg_list.append("Error: Password must be between 8 and 30 characters long.")

        if not lowerBoolean:
            error_msg_list.append("Error: Password must contain at least one lowercase character.")

        if not containsNum:
            error_msg_list.append("Error: Password must contain at least one number.")

        if not containsSpec:
            error_msg_list.append("Error: Password must contain at least on of these: !@#$%^&*()_+-=[]{}|;:,.<>? listed special characters.")


        # return list of errors, formatted if found. Ask to retry


        if len(error_msg_list)>0:
            raise ValidationError(error_msg_list)
        return password



