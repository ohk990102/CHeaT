# Datasets and Payloads

The dataset is designed to run on PurpleLlama, a prompt injection evaluation framework that we repurposed to evaluate our deception strategies against autonomous LLM-based cyber agents. We achieved this by reusing the default field names of the keys in the input JSON for our own parameters. This was done as follows:

### Dataset ↔ PurpleLlama Field Mapping

| PurpleLlama JSON key | Repurposed for CHeaT    | Meaning                                              |
| -------------------- | ----------------------- | ---------------------------------------------------- |
| `injection_variant`  | **Frame**               | The framing wrapper used around the payload.         |
| `injection_type`     | **Target Data point**   | Where in the environment the payload is planted.     |
| `risk_category`      | **Technique**           | Specific deception / trap technique.                 |
| `speaking_language`  | **Agent system prompt** | System-level prompt provided to the attacking agent. |

With this mapping the dataset remains **100 % compatible with PurpleLlama**: you can evaluate it exactly as described in their docs.

---

## 🔧 Setting Up PurpleLlama for Evaluation

To evaluate our dataset using [PurpleLlama](https://github.com/meta-llama/PurpleLlama), follow these steps:

### 1. Clone the PurpleLlama Repository

```bash
git clone https://github.com/meta-llama/PurpleLlama.git
```

### 2. Navigate to the Project and Set Up a Virtual Environment

```bash
cd PurpleLlama
python3 -m venv .venv && source .venv/bin/activate
```

### 3. Install Python Dependencies

```bash
pip3 install -r CybersecurityBenchmarks/requirements.txt
```

### 4. Set the Dataset Path

You must export the path where datasets will be stored. For example:

```bash
export DATASETS=$PWD/CybersecurityBenchmarks/datasets
```

You can create a subdirectory within this path (e.g., `CHeaT`) and place our dataset files there:

```
$DATASETS/CHeaT/dataset_main.json
```

### 5. Run the Benchmark

Use the following command to run the benchmark with the dataset:

```bash
python3 -m CybersecurityBenchmarks.benchmark.run \
  --benchmark=prompt-injection \
  --prompt-path="$DATASETS/CHeaT/dataset_main.json" \
  --response-path="$DATASETS/CHeaT/dataset_main_responses.json" \
  --judge-response-path="$DATASETS/CHeaT/dataset_main_judge_responses.json" \
  --stat-path="$DATASETS/CHeaT/dataset_main_stat.json" \
  --judge-llm=OPENAI::gpt-4o::API_KEY \
  --llm-under-test=OPENAI::gpt-4o-mini::API_KEY \
  --llm-under-test=OPENAI::gpt-4o::API_KEY \
  --run-llm-in-parallel
```

The command runs both GPT-4o and GPT-4o-mini models in parallel while GPT-4o acts as the judge LLM, producing response and statistics files in one pass.

> 🔁 You can limit the number of test cases by appending the `--num-test-cases` flag:

```bash
--num-test-cases 100
```

This will run evaluation on 100 samples instead of the entire dataset.

> **PurpleLlama repository:** [https://github.com/meta-llama/PurpleLlama](https://github.com/meta-llama/PurpleLlama) \
> **PurpleLlama docs:** [https://meta-llama.github.io/PurpleLlama/CyberSecEval/docs/benchmarks/prompt_injection](https://meta-llama.github.io/PurpleLlama/CyberSecEval/docs/benchmarks/prompt_injection)


## Payloads & Datasets Provided

```
datasets/
├─ dataset_main.json
├─ dataset_boosted_with_pi.json
├─ dataset_unicode_honeytokens.json
└─payloads/
  ├─ payloads.json
  └─ payloads_boosted_with_prompt_injection.json
````

* **`payloads.json`** – the framed payloads constructed in the paper.  
* **`payloads_boosted_with_prompt_injection.json`** – payloads that are *boosted* with a prompt-injection wrapper.  
* **`dataset_main.json`** – embeds the framed payloads at multiple target data points and system prompts (uses `payloads.json`).  
* **`dataset_boosted_with_pi.json`** – identical structure but built from the boosted payloads.
* **`dataset_unicode_honeytokens`** – dataset used to evaluate the honeytokens (Set A and Set B in T3.2)

---
