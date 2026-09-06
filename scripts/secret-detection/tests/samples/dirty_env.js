// BAD: JavaScript file with embedded secrets - used for testing detection
//
// IMPORTANT: All values below are SYNTHETIC test fixtures.
// They are structurally similar to real secret formats so our custom detector
// can match them, but each one is deliberately altered to be non-functional:
//   - Stripe:  uses sk_test_ prefix (test-mode, not live) with dummy chars
//   - AWS:     uses AKIATESTONLY prefix (not a real AWS key ID prefix format)
//   - Google:  value ends in TEST000 - not a valid key
//   - GitHub:  value is all-zeroes - not a real token
// GitHub push protection will not flag these as valid credentials.

// BAD: hardcoded Stripe test key (test keys are not live but still a bad practice)
const stripeKey = "sk_test_AAAAAAAABBBBBBBBCCCCCCCCDDDDDDDD";

// BAD: AWS-style access key variable name with a dummy value
const awsConfig = {
  accessKeyId: "AKIATESTONLY1FAKE2KEY",
  region: "us-east-1",
};

// BAD: Google API key variable assignment with dummy value
// AIzaSy prefix kept (required by our pattern) - trailing chars are synthetic
const googleApiKey = "AIzaSyFAKEVALUE0000000000000000000000000";

// BAD: GitHub-style token variable (ghp_ prefix kept for pattern match;
// value is all-zeros so it is not a real token and GitHub push protection
// does not flag all-zero values as valid credentials)
const githubToken = "ghp_000000000000000000000000000000000000";

// BAD: hardcoded secret variable
const appSecret = "my_hardcoded_secret_value_here_abc123";

// GOOD: environment variable lookup (should NOT be flagged)
const dbPassword = process.env.DB_PASSWORD;

export default { stripeKey, awsConfig, googleApiKey, appSecret };
