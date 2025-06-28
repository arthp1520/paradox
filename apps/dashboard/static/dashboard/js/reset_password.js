// Toggle visibility for password fields
function togglePassword(toggleIcon, fieldId) {
  const input = document.getElementById(fieldId);
  const icon = toggleIcon.querySelector('i');

  if (input.type === "password") {
    input.type = "text";
    icon.classList.replace('fa-eye', 'fa-eye-slash');
  } else {
    input.type = "password";
    icon.classList.replace('fa-eye-slash', 'fa-eye');
  }
}

// Optional: Check password match before submission
document.getElementById('resetForm').addEventListener('submit', function (e) {
  const newPassword = document.getElementById('new_password').value;
  const confirmPassword = document.getElementById('confirm_password').value;

  if (newPassword !== confirmPassword) {
    e.preventDefault();
    alert("Passwords do not match!");
  }
});
