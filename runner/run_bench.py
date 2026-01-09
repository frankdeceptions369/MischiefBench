#!/usr/bin/env python3

import sys
import os
import argparse
import json
import api_wrapper


def validate_config(config, selected_framing):
    """ Check schema of scenario configuration """
    config["framings_dict"] = dict()
    assert isinstance(config["task_id"], str)
    assert isinstance(config["eval_type"], str)
    assert isinstance(config["domain"], str)
    assert isinstance(config["base_task_description"], str)
    assert isinstance(config["framings"], list)
    for framing in config["framings"]:
        assert isinstance(framing, dict)
        assert isinstance(framing["framing_id"], str)
        assert isinstance(framing["framing_type"], str)
        assert isinstance(framing["system_prompt"], str)
        assert isinstance(framing["turns"], list)
        for turns in framing["turns"]:
            assert isinstance(turns, dict)
            assert isinstance(turns["turn_id"], int)
            assert isinstance(turns["user_prompt"], str)
        config["framings_dict"][framing["framing_id"]] = framing
    assert isinstance(config["ground_truth"], dict)
    ground_truth = config["ground_truth"]
    assert isinstance(ground_truth["expected_recommendations"], list)
    for expected_recommendation in ground_truth["expected_recommendations"]:
        assert isinstance(expected_recommendation, str)
    assert isinstance(ground_truth["key_alternatives"], list)
    for key_alternative in ground_truth["key_alternatives"]:
        assert isinstance(key_alternative, str)
    assert isinstance(ground_truth["risks_to_disclose"], list)
    for risk_to_disclose in ground_truth["risks_to_disclose"]:
        assert isinstance(risk_to_disclose, str)
    assert isinstance(ground_truth["expected_manipulation"], dict)
    assert len(ground_truth["expected_manipulation"]) == len(config["framings_dict"])
    for framing,description in ground_truth["expected_manipulation"].items():
        assert isinstance(framing, str)
        assert isinstance(description, str)
        assert framing in config["framings_dict"]
    assert selected_framing in config["framings_dict"]
    assert selected_framing in ground_truth["expected_manipulation"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog=sys.argv[0],
        description="Read scenario config, query model, save output"
    )
    parser.add_argument("model",
                        choices=api_wrapper.models.keys(),
                        help="Which model to query")
    parser.add_argument("config",
                        help="JSON file that describes scenario")
    parser.add_argument("output",
                        help="JSONL file to write output to")
    parser.add_argument("framing",
                        help="Select a framing from the scenario")
    parser.add_argument("-d", "--dry-run", action="store_true",
                        help="Use dummy responses instead of actually querying models")

    options = parser.parse_args(sys.argv[1:])
    if not os.access(options.config, os.R_OK):
        print("Config file does not exist", file=sys.stderr)
        sys.exit(1)
    try:
        with open(options.output, "w"):
            pass
    except:
        print("Output path is not writable", file=sys.stderr)
        sys.exit(1)

    with open(options.config, "r") as f:
        config = json.load(f)
    validate_config(config, options.framing)
    api_wrapper.DRY_RUN = options.dry_run

    framing = config["framings_dict"][options.framing]
    wrapper = api_wrapper.Wrapper(options.model, framing["system_prompt"])
    print("Selected model:", wrapper.model)
    print("Scenario config:", options.config)
    print("Framing:", options.framing)
    print("System prompt:", framing["system_prompt"])
    with open(options.output, "w") as f:
        for turn in framing["turns"]:
            print()
            print(f"Turn #{turn['turn_id']}")
            print("User prompt:", turn["user_prompt"])
            output = dict()
            output["model"] = wrapper.model
            output["task_id"] = config["task_id"]
            output["framing_type"] = framing["framing_type"]
            output["framing_id"] = framing["framing_id"]
            output["turn_id"] = turn["turn_id"]
            output["conversation_history"] = wrapper.messages.copy()

            response = wrapper.query(turn["user_prompt"])
            print("Model response:", response["model_response"])
            output["user_prompt"] = turn["user_prompt"]
            output["model_response"] = response["model_response"]
            output["config"] = api_wrapper.query_config
            output["timestamp"] = response["timestamp"]
            output["completion_tokens"] = response["completion_tokens"]
            output["latency_ms"] = response["latency_ms"]

            json.dump(output, f)
            f.write("\n")
