import json
import os
import sys

# Define the path to the segments_data.json file
# Assuming this script is run from the backend root or similar, we'll try to find it relative to this script
# The script is expected to be placed in d:\Graphology\Master Software\Eduecosystem\backend\scripts
# So the data file should be in d:\Graphology\Master Software\Eduecosystem\backend\data\segments_data.json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
SEGMENTS_FILE = os.path.join(DATA_DIR, "segments_data.json")

print(f"Looking for segments file at: {SEGMENTS_FILE}")

KENA_CONTENT = """# Course: The Kena Upanishad – Monasticism, Causality, & The First Question
### Based on the Commentary of Adi Shankaracharya

## 1. Introduction and The Two Commentaries
The lecture begins with the Shanti Mantra (Peace Invocation). The narrator notes a linguistic nuance: the Hindi/Sanskrit pronunciation is Brahma ($Brahma$), not "Brah-muh."

### Shankaracharya’s Unique Contribution
Adi Shankaracharya wrote commentaries (Bhashyas) on ten principal Upanishads, the Brahma Sutras, and the Bhagavad Gita. However, for the Kena Upanishad, he uniquely wrote two commentaries:
*   **Pada Bhashya**: A word-by-word commentary (the focus of this lecture series).
*   **Vakya Bhashya**: A sentence-based explanation.

---

## 2. The Great Debate: Knowledge (Jnana) vs. Rituals (Karma)
Shankaracharya begins the Pada Bhashya by addressing a fundamental objection (Purva Paksha) raised by the ritualists.

### The Opponent’s Question
> "Why not combine Vedanta (Self-Knowledge) with Karmakanda (Rituals)? Why can one not pursue worldly prosperity/heaven via rituals while simultaneously pursuing Moksha (Liberation)?"

### Shankaracharya’s Refutation
Shankaracharya argues that Karma (Ritual/Action) and Jnana (Knowledge) cannot be combined because they operate on contradictory principles regarding Causality.

#### A. The Nature of Karmakanda (The Path of Rituals)
*   **Principle**: Causality (Cause and Effect).
*   **Mechanism**: If you perform a specific Dharma (Cause), you get Punya (Merit), which results in Sukha (Happiness). conversely, Adharma leads to Paapa and Dukha (Misery).
*   **The Limitation**: Everything produced by a cause is an effect. All effects are temporary. Therefore, rituals can only produce temporary results (Heaven, wealth, progeny).

#### B. The Marshmallow Experiment (Modern Analogy)
The narrator uses the famous Stanford Marshmallow experiment (Walter Mischel/Philip Zimbardo) to illustrate the instinctive understanding of causality.
*   **The Test**: Children were offered one marshmallow now, or two if they waited.
*   **The Result**: Children who waited showed an understanding of "Cause (Waiting) $\\rightarrow$ Effect (Greater Reward)."
*   **Long-term Data**: Years later, the children who exercised restraint generally performed better academically and socially.
*   **Connection to Vedas**: The Vedic ritualist is like the child waiting for the second marshmallow—they sacrifice immediate impulse for a greater future reward (Heaven). However, it is still within the realm of desire and results.

---

## 3. The Three Worlds (The Vedic Worldview)
Shankaracharya explains the specific goals (Sadhya) and means (Sadhana) of the Vedic ritualistic section.

### The Three Desires (Eshana)
The Vedas classify all human striving into three categories of results, achieved by three specific means.

| The Goal (Sadhya/Result) | The Means (Sadhana/Cause) | Nature |
| :--- | :--- | :--- |
| **1. Manusha Loka** (The Human World) | **Putra** (Progeny/Children) | Worldly |
| **2. Pitri Loka** (World of Ancestors) | **Karma** (Vedic Fire Rituals) | Other-Worldly |
| **3. Brahma Loka** (Highest Heaven) | **Vidya/Upasana** (Meditation) | Divine |

> [!WARNING]
> **The Limitation**: Shankaracharya points out that all three worlds—from Earth up to Brahma Loka—are "worlds of return" (Punaravartin). They are products of action, limited by time, and infected by fear of loss.

---

## 4. The Argument for Monasticism (Sannyasa)
Shankaracharya asserts that to attain Brahman, one must step out of the field of causality entirely.

### The Scriptural Basis
Shankara quotes the Brihadaranyaka Upanishad:
> "What shall we do with children, we who have attained this Self, this World (Atma-Loka)?"

### Why Renounce?
1.  **The Goal is Different**: The seeker of Brahman does not want the Human World, Ancestral Heaven, or Brahma Loka. They desire the Atman (Self).
2.  **Atman is Not an Effect**: The Self is Aja (Unborn), Amrita (Immortal), and Abhaya (Fearless).
3.  **Independence from Action**:
    *   No action (Karma) can increase the Atman.
    *   No action can decrease or harm the Atman.
    *   Therefore, rituals are useless for Self-Realization.

### The Definition of Formal Sannyasa
Shankaracharya argues that since Children, Rituals, and Meditation are the means to the three limited worlds, one who rejects those worlds must logically reject their means.
*   **Rejection of Putra (Children)** $\\rightarrow$ Implies Celibacy.
*   **Rejection of Karma (Rituals)** $\\rightarrow$ Implies giving up the "Sacrificial Fire" (Duties/Career).
*   **Rejection of Wealth** $\\rightarrow$ Implies Poverty.

**Conclusion**: Formal Monasticism (Sannyasa) in the Vedic context is the renunciation of the desire for the three worlds and the consequent renunciation of the activities (family/rituals) required to get there.

---

## 5. The Dialogue Format & The Guru
### Why a Dialogue?
Shankara notes that the Upanishad is presented as a conversation (Q&A) for two reasons:
1.  **Subtlety**: The subject is the subtlest of all knowledge; a dialogue makes it easier to comprehend.
2.  **Necessity of a Teacher**: One cannot argue their way to Enlightenment using pure reason (Tarka). It must be pointed out by an enlightened guide.

### The Qualifications of the Guru
The student must approach a Guru who possesses three specific qualities:
*   **Shrotriya**: Master of the Scriptures/Tradition.
*   **Brahma-nishtha**: Centered/Established in Brahman (Experience).
*   **Akamahata**: untouched by desire (Ethical purity).

### The Approach
The student approaches with "sacrificial wood in hand" (Samit-pani), symbolizing humility and service, asking for that which is Abhayam (Fearless) and Shivam (Good/Auspicious).

---

## 6. The Kena Upanishad: Mantra 1
The Upanishad opens with a profound question about the nature of Consciousness.

### The Mantra
> ॐ केनेषितं पतति प्रेषितं मनः ।
> केन प्राणः प्रथमः प्रैति युक्तः ।
> केनेषितां वाचमिमां वदन्ति ।
> चक्षुः श्रोत्रं क उ देवो युनक्ति ॥ १ ॥

> *Om keneshitam patati preshitam manah |*
> *Kena pranah prathamah praiti yuktah |*
> *Keneshitam vachamimam vadanti |*
> *Chakshuh shrotram ka u devo yunakti || 1 ||*

### Translation
> "Willed by whom does the directed mind go towards its object? Being directed by whom does the vital force (Prana) that precedes all, proceed? By whom is this speech willed that people utter? Who is the effulgent Being who directs the eyes and the ears?"

### Detailed Explanation of the Question
*   **The "Hard Problem" of Consciousness**: The student is not asking about the mechanism of hearing (physiology) or the process of thinking (psychology).
*   **The Source**: The student asks for the Subject—the "Shining Being" (Deva)—that makes the operation of the mind, breath, speech, and senses possible.
*   **The "Ask" vs. "Acts"**: The narrator shares an etymological insight: The word "Ask" implies both a request for information and a demand/command ("What is the 'Ask'?"). The root of asking is linked to the root of "seeing" or "shining" (Aksha).
*   **The Inquiry**: The student realizes that the eyes see and the mind thinks, but they are inert instruments. There must be a sentient principle behind them that "installs" them in their respective duties.

---

## 7. Key Statistics & Data Mentioned
*   **The Marshmallow Test**: Conducted by Walter Mischel and repeated by Philip Zimbardo with 4-year-olds. The follow-up study (14 years later) indicated a correlation between delayed gratification and life success.
*   **Nobel Prize in Physics/Chemistry (2024)**: Mentioned in the context of AI (AlphaFold, Demis Hassabis, etc.) aiding scientific discovery, yet even AI requires a "teacher" or human guidance (Terence Tao's grading of AI as a "not entirely hopeless grad student").
"""

def update_segments():
    try:
        if not os.path.exists(SEGMENTS_FILE):
            print(f"Error: File not found at {SEGMENTS_FILE}")
            # Initialize empty dict if not found
            data = {}
        else:
            with open(SEGMENTS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        
        # Target Key: 1_1_1_1 (Cycle 1, Day 1, Part 1, Segment 1)
        TARGET_KEY = "1_1_1_1"
        
        # Create or update the segment
        if TARGET_KEY not in data:
            data[TARGET_KEY] = {
                "title": "The Kena Upanishad – Monasticism & Causality",
                "key_points": KENA_CONTENT,
                "video_url": None, # Assuming no video for now, or keep existing if any
                "duration": "25:00",
                "updated_at": "2024-01-06T10:00:00Z"
            }
        else:
            data[TARGET_KEY]["title"] = "The Kena Upanishad – Monasticism & Causality"
            data[TARGET_KEY]["key_points"] = KENA_CONTENT
            # Keep other fields like video_url if they exist
            
        # Write back to file
        with open(SEGMENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
            
        print(f"Successfully updated segment {TARGET_KEY} in {SEGMENTS_FILE}")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    # Ensure directory exists
    os.makedirs(DATA_DIR, exist_ok=True)
    update_segments()
