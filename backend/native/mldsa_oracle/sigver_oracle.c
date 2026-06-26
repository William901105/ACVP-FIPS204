#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <mldsa_native.h>

static int hex_nibble(char value)
{
  if (value >= '0' && value <= '9')
  {
    return value - '0';
  }
  if (value >= 'a' && value <= 'f')
  {
    return value - 'a' + 10;
  }
  if (value >= 'A' && value <= 'F')
  {
    return value - 'A' + 10;
  }
  return -1;
}

static int parse_hex(const char *name, const char *hex, uint8_t *out,
                     size_t expected_bytes)
{
  size_t hex_len = strlen(hex);
  size_t i;

  if (hex_len != expected_bytes * 2)
  {
    fprintf(stderr, "%s must be exactly %zu hex characters\n", name,
            expected_bytes * 2);
    return -1;
  }

  for (i = 0; i < expected_bytes; i++)
  {
    int high = hex_nibble(hex[i * 2]);
    int low = hex_nibble(hex[(i * 2) + 1]);

    if (high < 0 || low < 0)
    {
      fprintf(stderr, "%s contains non-hex characters\n", name);
      return -1;
    }

    out[i] = (uint8_t)((high << 4) | low);
  }

  return 0;
}

static int parse_hex_alloc(const char *name, const char *hex, uint8_t **out,
                           size_t *out_len)
{
  size_t hex_len = strlen(hex);
  size_t byte_len;
  size_t i;

  if (hex_len % 2 != 0)
  {
    fprintf(stderr, "%s hex string must have an even number of characters\n",
            name);
    return -1;
  }

  byte_len = hex_len / 2;
  *out = NULL;
  *out_len = byte_len;

  if (byte_len == 0)
  {
    return 0;
  }

  *out = (uint8_t *)malloc(byte_len);
  if (*out == NULL)
  {
    fprintf(stderr, "failed to allocate %s buffer\n", name);
    return -1;
  }

  for (i = 0; i < byte_len; i++)
  {
    int high = hex_nibble(hex[i * 2]);
    int low = hex_nibble(hex[(i * 2) + 1]);

    if (high < 0 || low < 0)
    {
      fprintf(stderr, "%s contains non-hex characters\n", name);
      free(*out);
      *out = NULL;
      *out_len = 0;
      return -1;
    }

    (*out)[i] = (uint8_t)((high << 4) | low);
  }

  return 0;
}

static int parse_binary_flag(const char *name, const char *value, int *out)
{
  if (strcmp(value, "0") == 0)
  {
    *out = 0;
    return 0;
  }
  if (strcmp(value, "1") == 0)
  {
    *out = 1;
    return 0;
  }
  fprintf(stderr, "%s must be 0 or 1\n", name);
  return -1;
}

int main(int argc, char **argv)
{
  uint8_t pk[CRYPTO_PUBLICKEYBYTES];
  uint8_t sig[CRYPTO_BYTES];
  uint8_t mu[MLDSA_CRHBYTES];
  uint8_t *message = NULL;
  const uint8_t *input = NULL;
  size_t input_len = 0;
  int externalmu = 0;
  const char *pk_hex;
  const char *input_hex;
  const char *signature_hex;
  int rc;

  if (argc == 4)
  {
    pk_hex = argv[1];
    input_hex = argv[2];
    signature_hex = argv[3];
  }
  else if (argc == 5)
  {
    if (parse_binary_flag("externalmu", argv[1], &externalmu) != 0)
    {
      return 2;
    }
    pk_hex = argv[2];
    input_hex = argv[3];
    signature_hex = argv[4];
  }
  else
  {
    fprintf(stderr,
            "usage: %s <pk_hex> <message_hex> <signature_hex>\n"
            "   or: %s <externalmu> <pk_hex> <message_or_mu_hex> "
            "<signature_hex>\n",
            argv[0], argv[0]);
    return 2;
  }

  if (parse_hex("pk", pk_hex, pk, sizeof(pk)) != 0)
  {
    return 2;
  }

  if (externalmu)
  {
    if (parse_hex("mu", input_hex, mu, sizeof(mu)) != 0)
    {
      return 2;
    }
    input = mu;
    input_len = sizeof(mu);
  }
  else
  {
    if (parse_hex_alloc("message", input_hex, &message, &input_len) != 0)
    {
      return 2;
    }
    input = message;
  }

  if (parse_hex("signature", signature_hex, sig, sizeof(sig)) != 0)
  {
    free(message);
    return 2;
  }

  /*
   * Match the Phase 2-3 internal sigGen path: direct Sign_internal/Verify_internal
   * input, empty prefix, and matching externalmu flag.
   */
  rc = mldsa_verify_internal(sig, sizeof(sig), input, input_len, NULL, 0, pk,
                             externalmu);
  free(message);

  if (rc == MLD_ERR_OUT_OF_MEMORY)
  {
    fprintf(stderr, "mldsa_verify_internal failed: out of memory\n");
    return 1;
  }

  fputs(rc == 0 ? "{\"testPassed\":true}\n" : "{\"testPassed\":false}\n",
        stdout);
  return 0;
}
