"""
Simple Calculator App
A production-quality Kivy calculator with expression parsing and safe evaluation
"""

import re
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle
from kivy.animation import Animation
from kivy.properties import StringProperty, NumericProperty
from kivy.clock import Clock


class CalculatorLayout(BoxLayout):
    """Main calculator layout containing display and buttons"""
    
    display_text = StringProperty('0')
    last_result = NumericProperty(0)
    new_expression = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 20
        self.create_widgets()
        
    def create_widgets(self):
        """Create and arrange all UI components"""
        # Display
        self.display = Label(
            text='0',
            font_size='40sp',
            size_hint=(1, 0.2),
            halign='right',
            valign='middle'
        )
        self.display.bind(text=self.on_display_text)
        self.add_widget(self.display)
        
        # Button grid
        button_grid = GridLayout(cols=4, spacing=10, size_hint=(1, 0.8))
        
        # Button definitions: (text, row, col, colspan, background_color)
        buttons = [
            ('C', 0, 0, 1, (0.8, 0.2, 0.2, 1)),      # Clear - red
            ('DEL', 0, 1, 1, (0.9, 0.5, 0.1, 1)),    # Delete - orange
            ('/', 0, 2, 1, (0.2, 0.6, 0.8, 1)),      # Divide - blue
            ('*', 0, 3, 1, (0.2, 0.6, 0.8, 1)),      # Multiply - blue
            
            ('7', 1, 0, 1, (0.3, 0.3, 0.3, 1)),      # Numbers - dark gray
            ('8', 1, 1, 1, (0.3, 0.3, 0.3, 1)),
            ('9', 1, 2, 1, (0.3, 0.3, 0.3, 1)),
            ('-', 1, 3, 1, (0.2, 0.6, 0.8, 1)),      # Subtract - blue
            
            ('4', 2, 0, 1, (0.3, 0.3, 0.3, 1)),
            ('5', 2, 1, 1, (0.3, 0.3, 0.3, 1)),
            ('6', 2, 2, 1, (0.3, 0.3, 0.3, 1)),
            ('+', 2, 3, 1, (0.2, 0.6, 0.8, 1)),      # Add - blue
            
            ('1', 3, 0, 1, (0.3, 0.3, 0.3, 1)),
            ('2', 3, 1, 1, (0.3, 0.3, 0.3, 1)),
            ('3', 3, 2, 1, (0.3, 0.3, 0.3, 1)),
            ('=', 3, 3, 1, (0.2, 0.8, 0.3, 1)),      # Equals - green (highlighted)
            
            ('0', 4, 0, 2, (0.3, 0.3, 0.3, 1)),      # Zero - spans 2 columns
            ('.', 4, 2, 1, (0.3, 0.3, 0.3, 1)),
        ]
        
        # Create and add buttons to grid
        for text, row, col, colspan, bg_color in buttons:
            btn = CalculatorButton(
                text=text,
                background_color=bg_color,
                colspan=colspan
            )
            btn.bind(on_press=self.on_button_press)
            button_grid.add_widget(btn)
        
        self.add_widget(button_grid)
    
    def on_display_text(self, instance, value):
        """Update display text with proper formatting"""
        self.display.text = value
    
    def on_button_press(self, instance):
        """Handle button press events with animation"""
        self.animate_button(instance)
        self.process_input(instance.text)
    
    def animate_button(self, button):
        """Add press animation to button"""
        anim = Animation(
            background_color=[c * 0.7 for c in button.background_color[:3]] + [1],
            duration=0.1
        )
        anim += Animation(
            background_color=button.original_color,
            duration=0.1
        )
        anim.start(button)
    
    def process_input(self, value):
        """Process calculator input based on button pressed"""
        current_text = self.display_text
        
        if self.new_expression and value not in '+-*/':
            # Start new expression after getting a result
            if value.isdigit() or value == '.':
                self.display_text = value
                self.new_expression = False
            return
        
        if value == 'C':
            # Clear everything
            self.display_text = '0'
            self.last_result = 0
            self.new_expression = True
            
        elif value == 'DEL':
            # Delete last character
            if len(current_text) > 1:
                self.display_text = current_text[:-1]
            else:
                self.display_text = '0'
                
        elif value == '=':
            # Evaluate expression
            self.evaluate_expression()
            
        elif value in '+-*/':
            # Handle operators
            if current_text and current_text[-1] in '+-*/':
                # Replace last operator
                self.display_text = current_text[:-1] + value
            else:
                self.display_text = current_text + value
            self.new_expression = False
            
        else:
            # Handle numbers and decimal point
            if current_text == '0' and value != '.':
                self.display_text = value
            else:
                # Prevent multiple decimal points in a number
                if value == '.':
                    # Find the last number in the expression
                    parts = re.split(r'([+\-*/])', current_text)
                    last_part = parts[-1] if parts else ''
                    if '.' in last_part:
                        return  # Already has decimal, ignore
                
                self.display_text = current_text + value
            self.new_expression = False
    
    def evaluate_expression(self):
        """Safely evaluate the mathematical expression"""
        expression = self.display_text
        
        # Remove any trailing operators
        while expression and expression[-1] in '+-*/':
            expression = expression[:-1]
        
        if not expression:
            self.display_text = '0'
            return
        
        try:
            # Sanitize and validate expression
            if not self.is_safe_expression(expression):
                self.display_text = 'Error'
                return
            
            # Evaluate using Python's eval with safe context
            result = eval(expression, {"__builtins__": {}}, {})
            
            # Format result
            if isinstance(result, (int, float)):
                if result == float('inf') or result == float('-inf'):
                    self.display_text = 'Error'
                elif result == int(result):
                    # Remove .0 for integer results
                    formatted_result = str(int(result))
                else:
                    formatted_result = str(result)
                
                self.display_text = formatted_result
                self.last_result = result
                self.new_expression = True
            else:
                self.display_text = 'Error'
                
        except ZeroDivisionError:
            self.display_text = 'Error: Div/0'
            self.new_expression = True
        except (SyntaxError, NameError, TypeError, ValueError):
            self.display_text = 'Error'
            self.new_expression = True
    
    def is_safe_expression(self, expression):
        """Validate that expression contains only safe characters and patterns"""
        # Allow only numbers, basic operators, and decimal points
        safe_pattern = r'^[\d+\-*/.()\s]+$'
        
        # Check for consecutive operators (except scientific notation, but we don't handle that)
        if re.search(r'[+\-*/]{2,}', expression):
            return False
            
        # Check for invalid decimal usage
        if re.search(r'\.\d*\.', expression):  # Multiple dots in a number
            return False
            
        # Check for operators at start (except minus for negative numbers)
        if expression and expression[0] in '+*/':
            return False
            
        # Check parentheses balance (basic check)
        if expression.count('(') != expression.count(')'):
            return False
            
        return bool(re.match(safe_pattern, expression))


class CalculatorButton(Button):
    """Custom button class for calculator with enhanced styling"""
    
    def __init__(self, colspan=1, **kwargs):
        super().__init__(**kwargs)
        self.colspan = colspan
        self.original_color = self.background_color
        self.font_size = '30sp'
        self.background_normal = ''
        
        # Bind size to update background
        self.bind(pos=self.update_bg, size=self.update_bg)
        
    def update_bg(self, *args):
        """Update button background with rounded corners"""
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.background_color)
            RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[20]
            )


class CalculatorApp(App):
    """Main Kivy application class"""
    
    def build(self):
        """Build and return the root widget"""
        Window.clearcolor = (0.1, 0.1, 0.1, 1)  # Dark background
        return CalculatorLayout()
    
    def on_pause(self):
        """Handle app pausing (important for mobile)"""
        return True
    
    def on_resume(self):
        """Handle app resuming"""
        pass


if __name__ == '__main__':
    CalculatorApp().run()