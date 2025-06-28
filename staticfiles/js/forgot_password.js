// Validate email format
function validateEmail(input) {
  const feedback = document.getElementById('emailFeedback');
  const email = input.value;
  const pattern = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

  if (!email) {
    feedback.textContent = "Email is required.";
    feedback.classList.add('text-danger');
    return false;
  }

  if (!pattern.test(email)) {
    feedback.textContent = "Please enter a valid email address.";
    feedback.classList.add('text-danger');
    return false;
  }

  feedback.textContent = "Email looks good!";
  feedback.classList.remove('text-danger');
  feedback.classList.add('text-success');
  return true;
}

// Prevent form submission if email is invalid
function handleForgotSubmit(event) {
  const emailInput = document.getElementById('email');
  const isValid = validateEmail(emailInput);
  if (!isValid) {
    event.preventDefault();
    alert("Please enter a valid email before submitting.");
    return false;
  }
  return true;
}
