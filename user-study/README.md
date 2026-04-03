# Study Design

## Overview

This directory contains the materials for a controlled user study comparing two approaches for interpreting two-dimensional embeddings:
1. **Orange**: An interactive data mining toolkit for exploratory data analysis
2. **VERA**: Static visual explanations via region annotation

The study uses a counterbalanced design in which the two approaches are alternated across dataset groups to reduce fatigue and other order effects.

## Study Structure

Participants were randomly assigned into two groups. Both groups saw the same six datasets in the same order. However, Group 1 used Orange for the first three datasets and VERA for the last three, whereas Group 2 used VERA for the first three and Orange for the second three. This design makes the comparison between tools fairer by balancing possible fatigue or order effects across the two tools.

### Study Phases

The study consists of the following phases for each group:

1. **Tutorial**: Participants received a brief tutorial on both tools.
1. **First Tool Introduction**: Instructions on how to proceed using their first tool
2. **First Dataset Group**: Three quizzes using the first tool
3. **Survey Phase**: Participants completed a survey about their experience with the first tool
4. **Second Tool Introduction**: Instructions on how to proceed using their second tool
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

| Step | Group 1 | Group 2 |
|---|---|---|
| Tutorial | | |
| Introduction | [Orange Introduction](orange-introduction.md) | [VERA Introduction](vera-introduction.md) |
| [Iris Quiz](quiz-1-iris.md) | *Orange* | [*VERA explanations*](vera-explanations/vera_explanations_iris.pdf) |
| [Employee Attrition Quiz](quiz-2-employee-attrition.md) | *Orange* | [*VERA explanations*](vera-explanations/vera_explanations_attrition.pdf) |
| [Raisin Quiz](quiz-3-raisin.md) | *Orange* | [*VERA explanations*](vera-explanations/vera_explanations_raisin.pdf) |
| Tool Survey | [Orange Survey](orange-survey.md) | [VERA Survey](vera-survey.md) |
| Introduction | [VERA Introduction](vera-introduction.md) | [Orange Introduction](orange-introduction.md) |
| [Penguins Quiz](quiz-1-penguins.md) | [*VERA explanations*](vera-explanations/vera_explanations_penguins.pdf) | *Orange* |
| [Titanic Quiz](quiz-2-titanic.md) | [*VERA explanations*](vera-explanations/vera_explanations_titanic.pdf) | *Orange* |
| [Wine Quality Quiz](quiz-3-wine-quality.md) | [*VERA explanations*](vera-explanations/vera_explanations_wine_quality.pdf) | *Orange* |
| Tool Survey | [VERA Survey](vera-survey.md) | [Orange Survey](orange-survey.md) |
| [Final Survey](final-survey.md) | | |

## Quiz Navigation

When completing the quizzes, note that some questions refer to the figure immediately preceding the question. These figures provide visual context for answering the corresponding question.
