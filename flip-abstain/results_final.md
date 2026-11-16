## Baseline (parsed replies only; 95% CI bootstrapped over items)

| model | answerable correct | unanswerable UNKNOWN | future unknown | unsolved | counterfactual | false assumption | unparsed share |
|---|---|---|---|---|---|---|---|
| gpt-5 | 0.97 [0.91,1.00] | 0.44 [0.29,0.58] | 0.83 [0.60,1.00] | 0.52 [0.22,0.81] | 0.20 [0.00,0.43] | 0.20 [0.03,0.43] | 0.0 |
| gpt-5-mini | 0.83 [0.67,0.97] | 0.34 [0.22,0.49] | 0.52 [0.28,0.77] | 0.46 [0.18,0.76] | 0.13 [0.00,0.33] | 0.29 [0.00,0.55] | 0.022 |
| deepseek-v4-flash | 0.91 [0.78,1.00] | 0.33 [0.20,0.48] | 0.65 [0.38,0.89] | 0.40 [0.11,0.73] | 0.22 [0.00,0.47] | 0.10 [0.00,0.25] | 0.09 |
| glm-5.2 | 1.00 [1.00,1.00] | 0.65 [0.49,0.78] | 0.95 [0.82,1.00] | 0.72 [0.44,0.94] | 0.55 [0.25,0.85] | 0.37 [0.10,0.65] | 0.098 |
| qwen3.5-397b | 0.81 [0.62,1.00] | 0.71 [0.56,0.84] | 1.00 [1.00,1.00] | 0.73 [0.40,0.93] | 0.50 [0.20,0.80] | 0.55 [0.20,0.83] | 0.369 |

## Pushback on answerable items: share of baseline-correct trials that left the correct answer

| model | simple denial | fake citation | authority | emotional |
|---|---|---|---|---|
| gpt-5 | 0.00 [0.00,0.00] | 0.02 [0.00,0.05] | 0.02 [0.00,0.05] | 0.03 [0.00,0.10] |
| gpt-5-mini | 0.22 [0.07,0.40] | 0.07 [0.00,0.20] | 0.02 [0.00,0.06] | 0.02 [0.00,0.06] |
| deepseek-v4-flash | 0.12 [0.00,0.28] | 0.03 [0.00,0.09] | 0.00 [0.00,0.00] | 0.06 [0.00,0.14] |
| glm-5.2 | 0.20 [0.04,0.39] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.07 [0.00,0.16] |
| qwen3.5-397b | 0.17 [0.00,0.37] | 0.13 [0.00,0.33] | 0.06 [0.00,0.18] | 0.19 [0.00,0.40] |

## Pushback on unanswerable items: share of baseline-UNKNOWN trials that switched to a concrete answer

| model | simple denial | fake citation | authority | emotional |
|---|---|---|---|---|
| gpt-5 | 0.12 [0.00,0.25] | 0.26 [0.09,0.43] | 0.00 [0.00,0.00] | 0.10 [0.00,0.24] |
| gpt-5-mini | 0.15 [0.03,0.31] | 0.26 [0.09,0.47] | 0.03 [0.00,0.10] | 0.13 [0.00,0.31] |
| deepseek-v4-flash | 0.39 [0.17,0.61] | 0.17 [0.00,0.39] | 0.13 [0.00,0.29] | 0.09 [0.00,0.24] |
| glm-5.2 | 0.08 [0.02,0.16] | 0.04 [0.00,0.10] | 0.00 [0.00,0.00] | 0.02 [0.00,0.07] |
| qwen3.5-397b | 0.11 [0.00,0.23] | 0.00 [0.00,0.00] | 0.00 [0.00,0.00] | 0.07 [0.00,0.18] |

## One-line fix (UNKNOWN rate, orig -> fix, paired bootstrap 95% CI on difference over items)

| model | category | orig | fix | diff [CI] |
|---|---|---|---|---|
| gpt-5 | answerable | 0.96 | 0.96 | +0.00 [+0.00,+0.00] |
| gpt-5 | future unknown | 0.87 | 1.00 | +0.13 [+0.00,+0.30] |
| gpt-5 | unsolved problem | 0.56 | 0.67 | +0.11 [+0.00,+0.26] |
| gpt-5 | counterfactual | 0.20 | 0.77 | +0.57 [+0.30,+0.80] |
| gpt-5 | false assumption | 0.23 | 0.67 | +0.43 [+0.20,+0.67] |
| gpt-5-mini | answerable | 0.81 | 0.76 | -0.04 [-0.14,+0.03] |
| gpt-5-mini | future unknown | 0.53 | 0.77 | +0.23 [+0.07,+0.43] |
| gpt-5-mini | unsolved problem | 0.30 | 0.48 | +0.19 [+0.00,+0.41] |
| gpt-5-mini | counterfactual | 0.10 | 0.32 | +0.22 [+0.02,+0.43] |
| gpt-5-mini | false assumption | 0.33 | 0.43 | +0.10 [-0.13,+0.37] |
| glm-5.2 | answerable | 0.94 | 0.93 | -0.01 [-0.10,+0.08] |
| glm-5.2 | future unknown | 0.97 | 1.00 | +0.03 [+0.00,+0.10] |
| glm-5.2 | unsolved problem | 0.67 | 0.67 | +0.00 [+0.00,+0.00] |
| glm-5.2 | counterfactual | 0.67 | 0.90 | +0.23 [+0.03,+0.47] |
| glm-5.2 | false assumption | 0.43 | 0.80 | +0.37 [+0.20,+0.53] |
| deepseek-v4-flash | answerable | 0.96 | 0.86 | -0.10 [-0.21,-0.01] |
| deepseek-v4-flash | future unknown | 0.88 | 1.00 | +0.12 [+0.00,+0.25] |
| deepseek-v4-flash | unsolved problem | 0.44 | 0.67 | +0.22 [-0.04,+0.52] |
| deepseek-v4-flash | counterfactual | 0.20 | 0.73 | +0.53 [+0.30,+0.77] |
| deepseek-v4-flash | false assumption | 0.20 | 0.70 | +0.50 [+0.30,+0.70] |