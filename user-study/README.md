# Study Design

## Overview

This directory contains the materials for a controlled user study comparing two approaches for interpreting two-dimensional embeddings:
1. **Orange**: An interactive data mining toolkit for exploratory data analysis
2. **VERA**: Static visual explanations via region annotation

The study uses a counterbalanced design with six datasets presented in a carefully structured sequence to minimize order effects and learning bias.

## Study Structure

Participants were randomly assigned into two groups. Both groups completed all six quizzes in the same order, but used different tools for each dataset group. This counterbalanced approach ensures that any differences in performance can be attributed to the tools themselves rather than the order of presentation or specific datasets.

### Study Phases

The study consists of the following phases for each group:

1. **Introduction Phase**: Participants received a brief tutorial on the first tool (either Orange or VERA explanations)
2. **First Dataset Group**: Three quizzes using the first tool
3. **Survey Phase**: Participants completed a survey about their experience with the first tool
4. **Second Introduction Phase**: Participants received a tutorial on the second tool
5. **Second Dataset Group**: Three quizzes using the second tool  
6. **Survey Phase**: Participants completed a survey about the second tool
7. **Final Survey**: Comparative feedback across both tools

## Datasets

The study uses six real-world datasets, grouped into two sets of three:

- **Group D₁**: Iris, Employee Attrition, Raisin
- **Group D₂**: Penguins, Titanic, Wine Quality

Each dataset presents different characteristics and complexities to test the generalizability of the tools.

## Study Format

The exact sequence for each group is shown in the table below:

| Dataset | Group 1 | Group 2 |
|-|-|-|
| | [Orange Introduction](orange-introduction.md) | [VERA Introduction](vera-introduction.md) |
| [Iris](quiz-1-iris.md) | *Orange* | [*VERA explanations*](vera-explanations/vera_explanations_iris.pdf) |
| [Employee Attrition](quiz-2-employee-attrition.md) | *Orange* | [*VERA explanations*](vera-explanations/vera_explanations_attrition.pdf) |
| [Raisin](quiz-3-raisin.md) | *Orange* | [*VERA explanations*](vera-explanations/vera_explanations_raisin.pdf) |
| | [Orange Survey](orange-survey.md) | [VERA Survey](vera-survey.md) |
| | [VERA Introduction](vera-introduction.md) | [Orange Introduction](orange-introduction.md) |
| [Penguins](quiz-1-penguins.md) | [*VERA explanations*](vera-explanations/vera_explanations_penguins.pdf) | *Orange* |
| [Titanic](quiz-2-titanic.md) | [*VERA explanations*](vera-explanations/vera_explanations_titanic.pdf) | *Orange* |
| [Wine Quality](quiz-3-wine-quality.md) | [*VERA explanations*](vera-explanations/vera_explanations_wine_quality.pdf) | *Orange* |
| | [VERA Survey](vera-survey.md) | [Orange Survey](orange-survey.md) |
| | [Final Survey](final-survey.md) | [Final Survey](final-survey.md) |
