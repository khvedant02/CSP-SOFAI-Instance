class ImprovementTrendEvaluator:
    def __init__(self):
        self.previous_feedback = None
        self.current_feedback = None
        self.no_improvement_flag = False

    def update_feedback(self, new_feedback):
        """Update the evaluator with new feedback from the validator."""
        # Shift current feedback to previous and update current with new feedback
        self.previous_feedback = self.current_feedback
        self.current_feedback = new_feedback
        self.evaluate_improvement()

    def evaluate_improvement(self):
        """Check if there is any improvement in the feedback."""
        if self.previous_feedback is not None and self.current_feedback is not None:
            # Set flag to True if there is no improvement (same errors)
            if self.previous_feedback == self.current_feedback:
                self.no_improvement_flag = True
            else:
                self.no_improvement_flag = False

    def get_no_improvement_flag(self):
        """Return the no improvement flag status."""
        return self.no_improvement_flag

    def print_status(self):
        """Print the current status of improvement."""
        if self.no_improvement_flag:
            print("No improvement between the last two feedbacks.")
        else:
            print("Improvement detected or insufficient data for comparison.")

# # Example usage:
# if __name__ == "__main__":
#     evaluator = ImprovementTrendEvaluator()
    
#     # Example feedbacks from the validator
#     feedback1 = {'errors': [('A', 'B')]}  # First feedback from validator
#     feedback2 = {'errors': [('A', 'B')]}  # Second feedback from validator, identical to first
#     feedback3 = {'errors': [('C', 'D')]}  # Third feedback, different

#     # Update evaluator with feedbacks
#     evaluator.update_feedback(feedback1)
#     evaluator.update_feedback(feedback2)
#     evaluator.print_status()  # Expected to print no improvement message

#     # Update with new, different feedback
#     evaluator.update_feedback(feedback3)
#     evaluator.print_status()  # Expected to indicate improvement