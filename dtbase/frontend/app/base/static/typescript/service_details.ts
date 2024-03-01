export function validateJSON(
  event: Event,
  buttonsToDisable: HTMLButtonElement[] = []
) {
  const target = event.target as HTMLTextAreaElement;
  let valid = true;
  try {
    JSON.parse(target.value);
  } catch (e) {
    valid = false;
  }
  // is-invalid is a bootstrap class
  if (!valid) {
    target.classList.add("is-invalid");
  } else {
    target.classList.remove("is-invalid");
  }

  for (const button of buttonsToDisable) {
    button.disabled = !valid;
  }
}

declare global {
  interface Window {
    validateJSON: (event: Event) => void;
  }
}
window.validateJSON = validateJSON;
