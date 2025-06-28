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

function handleForgotSubmit(e) {
  const emailInput = document.getElementById('email');
  if (!emailInput.checkValidity()) {
    emailInput.classList.add("is-invalid");
    return false;
  }

  const button = document.querySelector("button[type='submit']");
  button.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Sending...`;
  button.disabled = true;

  return true;
}
