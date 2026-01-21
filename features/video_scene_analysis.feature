Feature: Video scene analysis

  Scenario: Video analysis runs when enabled
    Given a media orchestrator with video analysis enabled
    When processing input with a video path
    Then the video pipeline is invoked
