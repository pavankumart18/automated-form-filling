from narration_generator import generate_audio_gemini

TEXT = "There's a saying in the markets: a company's price is an opinion, but its data is the truth. To find the truth, we need the right magnifying glass."

print("Calling generate_audio_gemini for test...")
output_file = generate_audio_gemini(TEXT, "output/screener_story_test_fixed")

if output_file:
    print(f"\nSUCCESS! Audio saved cleanly to: {output_file}")
else:
    print("\nFAILED: Return was None (hit quota limits repeatedly).")
