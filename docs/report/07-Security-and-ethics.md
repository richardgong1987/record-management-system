## Security and Ethics

The system saves personally identifiable information, including client names, phone numbers, and postal addresses, in a plaintext
JSONL file without encryption or access controls.

In a real deployment, this would conflict with data protection legislation such as the UK General Data Protection Regulation, which requires personal data to be processed in a manner that ensures appropriate security and protection against unauthorised access (UK GDPR, 2016).

Clients provide personal information with a reasonable expectation of privacy, and storing such data in an unprotected file introduces both security and ethical concerns. A production-ready implementation would therefore require safeguards such as encryption, authentication, and controlled file access before deployment.
