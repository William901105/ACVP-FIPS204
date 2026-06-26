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

static void print_hex_upper(const uint8_t *buffer, size_t length)
{
  static const char hex[] = "0123456789ABCDEF";
  size_t i;

  for (i = 0; i < length; i++)
  {
    fputc(hex[buffer[i] >> 4], stdout);
    fputc(hex[buffer[i] & 0x0F], stdout);
  }
}

int main(int argc, char **argv)
{
  uint8_t sk[CRYPTO_SECRETKEYBYTES];
  uint8_t sig[CRYPTO_BYTES];
  uint8_t rnd[MLDSA_RNDBYTES] = {0};
  uint8_t mu[MLDSA_CRHBYTES];
  uint8_t *message = NULL;
  const uint8_t *input = NULL;
  size_t input_len = 0;
  size_t siglen = 0;
  int externalmu = 0;
  int deterministic = 1;
  const char *sk_hex;
  const char *input_hex;
  const char *rnd_hex = NULL;
  int rc;

  if (argc == 3)
  {
    sk_hex = argv[1];
    input_hex = argv[2];
  }
  else if (argc == 5 || argc == 6)
  {
    if (parse_binary_flag("externalmu", argv[1], &externalmu) != 0 ||
        parse_binary_flag("deterministic", argv[2], &deterministic) != 0)
    {
      return 2;
    }

    if (deterministic && argc != 5)
    {
      fprintf(stderr, "rnd_hex is not allowed when deterministic=1\n");
      return 2;
    }
    if (!deterministic && argc != 6)
    {
      fprintf(stderr, "rnd_hex is required when deterministic=0\n");
      return 2;
    }

    sk_hex = argv[3];
    input_hex = argv[4];
    if (!deterministic)
    {
      rnd_hex = argv[5];
    }
  }
  else
  {
    fprintf(stderr,
            "usage: %s <sk_hex> <message_hex>\n"
            "   or: %s <externalmu> <deterministic> <sk_hex> "
            "<message_or_mu_hex> [rnd_hex]\n",
            argv[0], argv[0]);
    return 2;
  }

  if (parse_hex("sk", sk_hex, sk, sizeof(sk)) != 0)
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

  if (rnd_hex != NULL && parse_hex("rnd", rnd_hex, rnd, sizeof(rnd)) != 0)
  {
    free(message);
    return 2;
  }

  /*
   * ACVP internal sigGen targets FIPS 204 Algorithm 7 ML-DSA.Sign_internal.
   * externalmu=0 consumes the ACVP message. externalmu=1 consumes the ACVP mu.
   * The randomized Phase 2-5 path is controlled only by the provided rnd bytes.
   */
  rc = mldsa_signature_internal(sig, &siglen, input, input_len, NULL, 0, rnd, sk,
                                externalmu);
  free(message);

  if (rc != 0)
  {
    fprintf(stderr, "mldsa_signature_internal failed: %d\n", rc);
    return 1;
  }
  if (siglen != sizeof(sig))
  {
    fprintf(stderr, "signature length mismatch: got %zu bytes, expected %zu\n",
            siglen, sizeof(sig));
    return 1;
  }

  fputs("{\"signature\":\"", stdout);
  print_hex_upper(sig, sizeof(sig));
  fputs("\"}\n", stdout);

  return 0;
}
