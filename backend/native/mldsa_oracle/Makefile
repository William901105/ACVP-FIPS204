.PHONY: all clean
.DEFAULT_GOAL := all

CC := clang
MLDSA_NATIVE_DIR ?= /root/ACVP204/mldsa-native
MLDSA_DIR := $(MLDSA_NATIVE_DIR)/mldsa

CPPFLAGS := \
	-I$(MLDSA_DIR) \
	-I$(MLDSA_DIR)/src \
	-DMLD_CONFIG_NAMESPACE_PREFIX=mldsa \
	-DMLD_CONFIG_NO_RANDOMIZED_API \
	-DMLD_CONFIG_NO_SIGN_API \
	-DMLD_CONFIG_NO_VERIFY_API

CFLAGS := \
	-std=c99 \
	-O3 \
	-Wall \
	-Wextra \
	-Wpedantic \
	-Werror=unused-result \
	-Wno-unknown-pragmas

MLDSA_SOURCES := \
	$(MLDSA_DIR)/src/ct.c \
	$(MLDSA_DIR)/src/debug.c \
	$(MLDSA_DIR)/src/packing.c \
	$(MLDSA_DIR)/src/poly.c \
	$(MLDSA_DIR)/src/poly_kl.c \
	$(MLDSA_DIR)/src/polyvec.c \
	$(MLDSA_DIR)/src/polyvec_lazy.c \
	$(MLDSA_DIR)/src/sign.c \
	$(MLDSA_DIR)/src/fips202/fips202.c \
	$(MLDSA_DIR)/src/fips202/fips202x4.c \
	$(MLDSA_DIR)/src/fips202/keccakf1600.c

ORACLE_SOURCE := keygen_oracle.c

BIN44 := bin/mldsa44_keygen_oracle
BIN65 := bin/mldsa65_keygen_oracle
BIN87 := bin/mldsa87_keygen_oracle

all: $(BIN44) $(BIN65) $(BIN87)

$(BIN44): CPPFLAGS += -DMLD_CONFIG_PARAMETER_SET=44
$(BIN65): CPPFLAGS += -DMLD_CONFIG_PARAMETER_SET=65
$(BIN87): CPPFLAGS += -DMLD_CONFIG_PARAMETER_SET=87

$(BIN44) $(BIN65) $(BIN87): $(ORACLE_SOURCE) $(MLDSA_SOURCES)
	mkdir -p $(@D)
	$(CC) $(CFLAGS) $(CPPFLAGS) $^ -o $@

clean:
	rm -rf bin
