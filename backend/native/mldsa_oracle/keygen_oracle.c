#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include <mldsa_native.h>

#define SEED_BYTES 32
#define SEED_HEX_CHARS (SEED_BYTES * 2)

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

static int parse_seed(const char *seed_hex, uint8_t seed[SEED_BYTES])
{
  size_t i;

  if (strlen(seed_hex) != SEED_HEX_CHARS)
  {
    fprintf(stderr, "seed must be exactly 64 hex characters\n");
    return -1;
  }

  for (i = 0; i < SEED_BYTES; i++)
  {
    int high = hex_nibble(seed_hex[i * 2]);
    int low = hex_nibble(seed_hex[(i * 2) + 1]);

    if (high < 0 || low < 0)
    {
      fprintf(stderr, "seed contains non-hex characters\n");
      return -1;
    }

    seed[i] = (uint8_t)((high << 4) | low);
  }

  return 0;
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
  uint8_t seed[SEED_BYTES];
  uint8_t pk[CRYPTO_PUBLICKEYBYTES];
  uint8_t sk[CRYPTO_SECRETKEYBYTES];
  int rc;

  if (argc != 2)
  {
    fprintf(stderr, "usage: %s <64-hex-char-seed>\n", argv[0]);
    return 2;
  }

  if (parse_seed(argv[1], seed) != 0)
  {
    return 2;
  }

  rc = mldsa_keypair_internal(pk, sk, seed);
  if (rc != 0)
  {
    fprintf(stderr, "mldsa_keypair_internal failed: %d\n", rc);
    return 1;
  }

  fputs("{\"pk\":\"", stdout);
  print_hex_upper(pk, sizeof(pk));
  fputs("\",\"sk\":\"", stdout);
  print_hex_upper(sk, sizeof(sk));
  fputs("\"}\n", stdout);

  return 0;
}
