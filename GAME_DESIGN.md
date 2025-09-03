# PL8WRDS: Game Design Document

## Core Concept
A digital license plate word game that captures the excitement of the classic car game while adding structured progression, social sharing, and competitive collection mechanics.

## Game Mechanics

### Two-Metric Plate System
Instead of a single "difficulty" score, each plate has two distinct attributes:

- **Quality Score**: Average ensemble score of all solutions (measures word impressiveness)
  - High quality = sophisticated vocabulary, rare words
  - Low quality = common, simple words
  
- **Solution Count**: Number of valid English words that can be formed
  - High count = many discovery opportunities, beginner-friendly
  - Low count = limited solutions, expert challenge

This creates four natural plate categories:
- **🏆 Legendary** (High Quality + Low Count): Tournament champions
- **💎 Premium** (High Quality + High Count): Discovery goldmines  
- **🎯 Training** (Medium Quality + High Count): Skill builders
- **⚡ Quick Win** (Low Quality + High Count): Confidence boosters

### Economic System

#### Free Core Experience
- **Daily free plate** - same for all players (Wordle-style)
- **Community challenges** - shared plates anyone can attempt
- **Basic gameplay** - no paywall for core word-finding experience

#### Coin Economy
**Earning Coins:**
- Daily plate completion: 50 coins
- Shared challenge attempts via your link: 10 coins each
- Community event participation: bonus coin rewards
- Achievement milestones: one-time rewards

**Spending Coins:**
- Unlock specific plates: 100-500 coins (based on quality/count)
- Hint purchases: 25 coins per hint
- Retry attempts: 10 coins to reset a failed plate
- Premium features: custom challenges, advanced analytics

**Optional Top-Up:**
- $0.99 → 100 coins (basic unlock pack)
- $4.99 → 600 coins (premium unlock pack)
- $9.99 → 1500 coins (power user pack)

### Competitive Collection

#### Plate Ownership Contests
- **Daily competitions** for premium plates
- **Winner takes ownership** based on highest score during competition window
- **Multiple scoring formats**: total points, best single word, unique solutions
- **Owned plates** can be traded or used in tournaments

#### Competition Windows
- **Flash contests**: 30-minute random drops
- **Daily auctions**: 24-hour competitions  
- **Weekly premiums**: 7-day contests for ultra-rare plates
- **Community events**: Everyone competes on the same challenging plate

### Social Features

#### Deep Link Sharing
**Challenge Links:**
```
pl8wrds.com/challenge/ABC?shared_by=player123&mode=help_request
```

**Sharing Motivations:**
- "I'm stuck - help me!" (collaborative problem-solving)
- "Bet you can't solve this" (competitive challenges)
- "Look what I'm working on" (progress sharing)

**Reward Structure:**
- Sharer gets coins when people attempt via their link
- Solver gets bonus points for helping
- Viral bonus for links that generate multiple attempts

#### Community Features
- Real-time leaderboards during competitions
- "Trending challenges" showing popular shared plates
- Collaboration mode where multiple players work on same plate
- Achievement system celebrating both individual and social accomplishments

## Core Gameplay Loop

### Daily Engagement
1. **Check daily free plate** (habit formation)
2. **Compete in active contests** for plates you want to own
3. **Attempt shared challenges** from friends/community
4. **Spend earned coins** on unlocking interesting plates
5. **Share challenging plates** to earn more coins

### Session Flow
1. **Plate appears** with letters displayed
2. **Time pressure** (inspired by car game urgency)
3. **Find words** that contain letters in correct order
4. **Score calculation** using ensemble algorithm
5. **Compare results** with other players
6. **Social sharing** of results or challenges

### Long-term Progression
- **Skill development** through increasingly challenging plates
- **Collection building** via contest victories and unlocks  
- **Social reputation** as a consistent solver/challenger
- **Vocabulary expansion** through exposure to sophisticated words

## Technical Implementation

### Plate Data Structure
Each plate contains:
- Letters (3-character combination)
- Quality score (average ensemble score)
- Solution count (number of valid words)
- Complete solution list with individual ensemble scores
- Competition history and current owner (if applicable)

### Social Integration
- Deep link generation for any plate
- Real-time leaderboards during competitions
- Share intent integration for mobile platforms
- Rich social media previews with plate statistics

### Monetization
- **Freemium model**: Core game always free
- **Convenience purchases**: Coins for immediate plate access
- **No artificial scarcity**: All content ultimately accessible through play
- **Respect player choice**: Patience vs payment options

## Success Metrics
- **Daily active users** engaging with free plates
- **Social sharing rate** and viral coefficient
- **Competition participation** and completion rates
- **Coin economy health** (earning vs spending balance)
- **Player retention** and session frequency
- **Educational impact** (vocabulary learning)

## Design Philosophy
- **Skill-based rewards** over pay-to-win mechanics
- **Social collaboration** alongside individual achievement  
- **Educational value** that provides lasting benefit
- **Respect for player time and choice**
- **Sustainable engagement** without exploitation
