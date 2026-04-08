#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>

/**
 * Write a program to find the least and greatest Hamming distances among all 
 * pairs of values in an array of 32 two-byte half-words. Assume all values are 
 * signed 16-bit (“half-word”) integers. The array of integers runs from data 
 * memory location 0 to 63. Even-numbered addresses are MSBs, following odd 
 * addresses are LSBs, e.g. a concatenation of addresses 0 and 1 forms a 16-bit 
 * two’s complement half-word. Write the minimum distance in location 64 and the 
 * maximum in 65.
 */

#define ARR_SIZE 6

void populate_mem(int8_t* mem) {
    // randomly generate values to be used 
    for (int i = 0; i < ARR_SIZE; i++) {
        (*mem) = (int8_t)((rand() & 0xFF));
        mem++;
    }
}

void to_binary(int8_t n, char *buffer) {
    for (int i = 7; i >= 0; i--) {
        // (n >> i) & 1: Shift the bit to the 0th position and check it
        buffer[7 - i] = (n & (1 << i)) ? '1' : '0';
    }
    buffer[8] = '\0';
}

int main() {
    int8_t mem[ARR_SIZE + 2];
    populate_mem(mem);

    for (int i = 0; i < ARR_SIZE; i++) {
        printf("mem[%d] = %d\n", i, mem[i]);
    }

    int8_t min_dist = 16; // largest possible distance is 16
    int8_t max_dist = 0;  // smallest possible distance is 0
    for (int i = 0; i < ARR_SIZE / 2; i++) {
        for (int j = i + 1; j < ARR_SIZE / 2; j++) {
            char msb1[9];
            char msb2[9];
            to_binary(mem[2*i], msb1);
            to_binary(mem[2*j], msb2);
            
            int8_t dist = 0;
            for (int c = 0; c < 8; c++) {
                dist += msb1[c]^msb2[c];
            }
            char lsb1[9];
            char lsb2[9];
            to_binary(mem[2*i + 1], lsb1);
            to_binary(mem[2*j + 1], lsb2);
            
            for (int c = 0; c < 8; c++) {
                dist += lsb1[c]^lsb2[c];
            }

            min_dist = min_dist < dist ? min_dist : dist;
            max_dist = max_dist > dist ? max_dist : dist;
        }
    }
    mem[ARR_SIZE] = min_dist;
    mem[ARR_SIZE + 1] = max_dist;

    printf("The minimum Hamming distance is %d\n", mem[ARR_SIZE]);
    printf("The maximum Hamming distance is %d\n", mem[ARR_SIZE + 1]);

    return 0;
}
