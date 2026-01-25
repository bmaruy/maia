"""
MAIA Prompt Perturbation System

This module provides tools for perturbing MAIA prompts to test robustness
and understand which prompt components are critical for performance.

Usage:
    from perturbations import apply_perturbations, restore_originals

    # Apply perturbations from config
    apply_perturbations('configs/my_test.yaml')

    # Restore original files
    restore_originals()
"""

from .perturber import apply_perturbations, restore_originals, clean_backups

__all__ = ['apply_perturbations', 'restore_originals', 'clean_backups']
