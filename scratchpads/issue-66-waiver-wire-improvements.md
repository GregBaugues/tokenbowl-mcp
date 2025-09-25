# Issue #66: Improve Waiver Wire Analysis Tools

**Issue Link**: https://github.com/GregBaugues/sleeper-mcp/issues/66

## Problem Summary

The current waiver wire analysis tools have critical issues:
1. **Context Pollution**: Tools return 5-10x more data than needed
2. **Missing Context**: No explanations for why players are trending
3. **Availability Errors**: Suggesting already-rostered players
4. **League Blind Spots**: Missing recently dropped players
5. **No Waiver Priority Analysis**: Not considering waiver position cost

## Implementation Plan

### Phase 1: Core Tool Updates (Priority)

#### 1.1 Modify `get_recent_transactions()`
- Add `drops_only` parameter to filter only drops
- Add `min_days_ago` and `max_days_ago` for date filtering
- Add `include_player_details` (default False) for minimal data mode
- Calculate `days_since` for drops

#### 1.2 Modify `get_waiver_wire_players()`
- Add `include_stats` parameter (default False) for minimal data
- Add `highlight_recent_drops` to mark recently dropped players
- Add `verify_availability` to double-check roster status
- Reduce default data returned to essential fields only

#### 1.3 Create `get_waiver_analysis()`
- Consolidate waiver analysis into single efficient tool
- Cross-reference all suggestions against current rosters
- Group by "recently_dropped_in_league" vs "trending_globally"
- Include current waiver priority and historical usage

### Phase 2: Intelligence Layer

#### 2.1 Implement `get_trending_context()`
- Use WebSearch to find why players are trending
- Look for injury news, depth chart changes, breakout performances
- Return concise 2-3 sentence summaries

#### 2.2 Add `evaluate_waiver_priority_cost()`
- Calculate if using waiver priority is worth it
- Consider projected points gain vs priority value
- Provide historical context on priority value

### Phase 3: Testing & Optimization

#### 3.1 Add comprehensive tests
- Unit tests for availability verification
- Tests for data minimization modes
- Integration tests with real league data

#### 3.2 Performance optimization
- Measure and reduce context usage (target: 80% reduction)
- Batch roster checks to avoid N+1 queries
- Add caching for recent drops (1 hour TTL)

## Implementation Steps

1. **Create feature branch**: `issue-66-waiver-improvements`
2. **Start with core modifications** to existing tools (backward compatible)
3. **Add new tools** one at a time with tests
4. **Verify context reduction** with benchmarks
5. **Test with real league data** to ensure accuracy
6. **Update documentation** with new features
7. **Create PR** with comprehensive testing

## Success Criteria

- [ ] Never suggest already-rostered players (0% errors)
- [ ] Reduce context usage by at least 70%
- [ ] All trending players have context explanations
- [ ] Recently dropped players are highlighted
- [ ] Waiver priority cost is considered
- [ ] All tests passing
- [ ] Documentation updated

## Technical Notes

- Maintain backward compatibility by adding optional parameters with sensible defaults
- Use minimal data mode by default, full data only when requested
- Cache recent drops to reduce API calls
- Gracefully handle web search failures for trending context
- Batch roster checks for performance

## Testing Strategy

### Unit Tests:
- Test availability checking logic
- Test data minimization modes
- Test drops_only filtering
- Test date range calculations

### Integration Tests:
- Full waiver analysis workflow
- Cross-reference with actual roster data
- Verify trending context fetching

### Manual Testing:
- Test with real league data
- Verify no rostered players are suggested
- Measure actual context usage reduction
- Confirm recently dropped players are identified

## Files to Modify

1. `/Users/greg/code/tokenbowl/sleeper-mcp/sleeper_mcp.py` - Main implementation
2. `/Users/greg/code/tokenbowl/sleeper-mcp/tests/test_sleeper_mcp.py` - Add tests
3. `/Users/greg/code/tokenbowl/sleeper-mcp/README.md` - Update documentation

## Deployment Considerations

- Changes are backward compatible
- New tools will auto-deploy to Render on merge to main
- Redis cache will help with performance
- Monitor for any rate limiting with web search integration