#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <time.h>

/**
 * Write a program to find the absolute values of the least and greatest 
 * arithmetic difference among all pairs of incoming values from Program 2. 
 * Assume again that all values are two’s complement (“signed”) 16-bit integers. 
 * The array of integers starts at location 0. Write the absolute value of the 
 * minimum difference in locations 66-67 and the maximum in 68-69. Format: 
 * mem[66] = MSB of smallest absolute value difference among pairs; 
 * mem[67] = LSB. 
 * mem[68] = MSB of largest absolute value difference among 
 * pairs, mem[69] = LSB.
 */

#define ARR_SIZE 6

void populate_mem(uint8_t* mem) {
    // randomly generate values to be used 
    for (int i = 0; i < ARR_SIZE; i++) {
        (*mem) = (uint8_t)((rand() & 0xFF));
        mem++;
    }
}

int main() {
    srand(time(NULL));

    uint8_t mem[ARR_SIZE + 6];
    populate_mem(mem);

    for (int i = 0; i < ARR_SIZE / 2; i++) {
        uint16_t msb = ((uint16_t)mem[2 * i]) << 8;
        uint16_t lsb = ((uint16_t)mem[2 * i + 1]);
        int16_t val = (int16_t)(msb | lsb & 0xFF);
        printf("mem[%d] = %d\n", 2 * i, val);
    }

    uint16_t min_dist = 65535; // 2^16 - 1
    uint16_t max_dist = 0;
    for (int i = 0; i < ARR_SIZE / 2; i++) {
        for (int j = i + 1; j < ARR_SIZE / 2; j++) {
            uint16_t msb1 = ((uint16_t)mem[2 * i]) << 8;
            uint16_t msb2 = ((uint16_t)mem[2 * j]) << 8;
            uint16_t lsb1 = ((uint16_t)mem[2 * i + 1]);
            uint16_t lsb2 = ((uint16_t)mem[2 * j + 1]);

            int16_t val1 = (int16_t)(msb1 | lsb1 & 0xFF);
            int16_t val2 = (int16_t)(msb2 | lsb2 & 0xFF);
            
            int16_t dist;
            if (val1 > val2) {
                dist = val1 - val2;
            } else {
                dist = val2 - val1;
            }

            min_dist = min_dist < dist ? min_dist : dist;
            max_dist = max_dist > dist ? max_dist : dist;
        }
    }

    mem[ARR_SIZE + 2] = (uint8_t)(min_dist >> 8);
    mem[ARR_SIZE + 3] = (uint8_t)(min_dist);
    mem[ARR_SIZE + 4] = (uint8_t)(max_dist >> 8);
    mem[ARR_SIZE + 5] = (uint8_t)(max_dist);

    printf("The minimum arithmetic distance is %d\n", min_dist);
    printf("The maximum arithmetic distance is %d\n", max_dist);

    return 0;
}
