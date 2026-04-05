import java.util.Random;
import java.util.Scanner;

public class JogoAdivinhacao {
    public static void main(String[] args) {
        Random random = new Random();

        int numeroSorteado = random.nextInt(100) + 1;
        int tentativas = 0;
        int palpite = 0;

        System.out.println("Bem-vindo ao Jogo de Adivinhação!");
        System.out.println("Um número entre 1 e 100 foi sorteado. Tente adivinhar!");

        while (palpite != numeroSorteado) {
            System.out.print("\nDigite o seu palpite: ");
            palpite = scanner.nextInt();
            tentativas++; 

            if (palpite < numeroSorteado) {
                System.out.println("O número sorteado é MAIOR que " + palpite + ".");
            } else if (palpite > numeroSorteado) {
                System.out.println("O número sorteado é MENOR que " + palpite + ".");
            } else {
                System.out.println("\n Parabéns! Você acertou o número " + numeroSorteado + "!");
                System.out.println("Você precisou de " + tentativas + " tentativa(s) para vencer.");
            }
        }

        scanner.close();
    }
}