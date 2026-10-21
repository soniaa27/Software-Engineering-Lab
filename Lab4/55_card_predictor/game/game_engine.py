import pygame
from game.deck import Deck

class GameEngine:
    STREAK_STEP = 2       # correct guesses needed to raise the multiplier
    MAX_MULTIPLIER = 5
    REVEAL_MS = 1200      # how long both cards stay on screen after a guess
    PROMPT_MSG = "Will the next card be HIGHER or LOWER?"

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.deck = Deck()

        self.current_card = self.deck.draw()
        self.next_card = None
        self.previous_card = None
        self.reveal_until = None   # tick time when the side-by-side reveal ends
        self.score = 0
        self.streak = 0
        self.status_msg = self.PROMPT_MSG
        self.status_color = (220, 220, 220)

        btn_w, btn_h = 140, 48
        self.btn_higher = pygame.Rect(width // 2 - btn_w - 20, height - 90, btn_w, btn_h)
        self.btn_lower = pygame.Rect(width // 2 + 20, height - 90, btn_w, btn_h)

        self.font_title = pygame.font.SysFont(None, 40)
        self.font_medium = pygame.font.SysFont(None, 30)
        self.font_small = pygame.font.SysFont(None, 24)

    @classmethod
    def multiplier_for(cls, streak):
        """Multiplier earned by the guess that brings the streak to `streak`."""
        if streak <= 0:
            return 1
        return min(1 + (streak - 1) // cls.STREAK_STEP, cls.MAX_MULTIPLIER)

    @property
    def multiplier(self):
        return self.multiplier_for(self.streak)

    @property
    def revealing(self):
        return self.reveal_until is not None

    def evaluate_guess(self, guess, now=None):
        """Draws next card, evaluates prediction and starts the reveal pause."""
        self.next_card = self.deck.draw()
        self._score_guess(guess)

        self.previous_card = self.current_card
        self.current_card = self.next_card
        if now is None:
            now = pygame.time.get_ticks()
        self.reveal_until = now + self.REVEAL_MS

    def _score_guess(self, guess):
        if self.next_card.numeric_rank == self.current_card.numeric_rank:
            # Tie: a PUSH leaves score and streak untouched.
            self.status_msg = f"PUSH! {self.next_card.rank_str} vs {self.current_card.rank_str}  No points won or lost"
            self.status_color = (220, 220, 220)
            return

        if guess == "HIGHER":
            correct = self.next_card.numeric_rank > self.current_card.numeric_rank
        else:
            correct = self.next_card.numeric_rank < self.current_card.numeric_rank
        if correct:
            self.streak += 1
            points = self.multiplier
            self.score += points
            self.status_msg = (
                f"CORRECT! {self.next_card.rank_str} vs {self.current_card.rank_str}"
                f"  +{points} (x{points})"
            )
            self.status_color = (80, 220, 80)
        else:
            lost_streak = self.streak
            self.streak = 0
            self.score = max(0, self.score - 1)
            self.status_msg = f"WRONG! {self.next_card.rank_str} vs {self.current_card.rank_str}"
            if lost_streak >= 2:
                self.status_msg += f"  Streak of {lost_streak} lost!"
            self.status_color = (235, 75, 75)

    def handle_event(self, event):
        if self.revealing:
            return  # ignore guesses until the comparison has been shown
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_higher.collidepoint(event.pos):
                self.evaluate_guess("HIGHER")
            elif self.btn_lower.collidepoint(event.pos):
                self.evaluate_guess("LOWER")

    def update(self, now=None):
        if not self.revealing:
            return
        if now is None:
            now = pygame.time.get_ticks()
        if now >= self.reveal_until:
            # Advance to the next round with the drawn card as the current card.
            self.reveal_until = None
            self.previous_card = None
            self.status_msg = self.PROMPT_MSG
            self.status_color = (220, 220, 220)

    def render(self, screen):
        screen.fill((25, 80, 45))

        title_surf = self.font_title.render("High-Low Card Predictor", True, (245, 245, 245))
        screen.blit(title_surf, (self.width // 2 - title_surf.get_width() // 2, 25))

        score_surf = self.font_medium.render(f"Score: {self.score}", True, (255, 220, 80))
        screen.blit(score_surf, (30, 30))

        streak_color = (255, 150, 50) if self.streak >= 1 + self.STREAK_STEP else (210, 210, 210)
        streak_surf = self.font_small.render(f"Streak: {self.streak}  x{self.multiplier}", True, streak_color)
        screen.blit(streak_surf, (30, 60))

        rem_surf = self.font_small.render(f"Deck: {self.deck.remaining} left", True, (210, 210, 210))
        screen.blit(rem_surf, (self.width - rem_surf.get_width() - 30, 35))

        card_w, card_h = 130, 180
        if self.revealing:
            gap = 50
            left_x = self.width // 2 - card_w - gap // 2
            right_x = self.width // 2 + gap // 2
            self.previous_card.render(screen, left_x, 100, card_w, card_h)
            self.current_card.render(screen, right_x, 100, card_w, card_h)

            for label, x in (("Previous", left_x), ("Drawn", right_x)):
                label_surf = self.font_small.render(label, True, (210, 210, 210))
                screen.blit(label_surf, (x + card_w // 2 - label_surf.get_width() // 2, 80))

            vs_surf = self.font_medium.render("vs", True, (245, 245, 245))
            screen.blit(vs_surf, (self.width // 2 - vs_surf.get_width() // 2, 100 + card_h // 2 - vs_surf.get_height() // 2))
        else:
            self.current_card.render(screen, self.width // 2 - card_w // 2, 100, card_w, card_h)

        status_surf = self.font_small.render(self.status_msg, True, self.status_color)
        screen.blit(status_surf, (self.width // 2 - status_surf.get_width() // 2, 310))

        # Buttons are greyed out while the reveal is on screen.
        higher_fill = (90, 100, 95) if self.revealing else (40, 140, 60)
        lower_fill = (90, 100, 95) if self.revealing else (170, 50, 50)

        pygame.draw.rect(screen, higher_fill, self.btn_higher, border_radius=8)
        pygame.draw.rect(screen, (220, 220, 220), self.btn_higher, width=2, border_radius=8)
        high_surf = self.font_medium.render("HIGHER", True, (255, 255, 255))
        screen.blit(
            high_surf,
            (self.btn_higher.centerx - high_surf.get_width() // 2, self.btn_higher.centery - high_surf.get_height() // 2),
        )

        pygame.draw.rect(screen, lower_fill, self.btn_lower, border_radius=8)
        pygame.draw.rect(screen, (220, 220, 220), self.btn_lower, width=2, border_radius=8)
        low_surf = self.font_medium.render("LOWER", True, (255, 255, 255))
        screen.blit(
            low_surf,
            (self.btn_lower.centerx - low_surf.get_width() // 2, self.btn_lower.centery - low_surf.get_height() // 2),
        )