/* Calculate the ANF of output defined over full internal state */

#include <iostream>
#include <algorithm>
#include <vector>
#include <bitset>
using namespace std;
typedef bitset<544> uint544; /* 554 = 93 + 84 + 111 + 128 + 128 */
typedef vector<uint544> Monomial;
typedef struct {
	int monomial_num;
	int degree;
	Monomial monomial;
} Poly;

/* For a given polynomial P, if a monomial M exsits in P, then remove M from P, else add M to P */
void remove_or_add_term(Poly &poly, uint544 monomial)  
{
	vector<bitset<544>>::iterator it = find(poly.monomial.begin(), poly.monomial.end(), monomial);
	if (it != poly.monomial.end())
	{
		poly.monomial.erase(it);
	}
	else
	{
		poly.monomial.push_back(monomial);
	}
}
int poly_degree(Poly &a)  /* calculate the algebraic degree of a given polynomial */
{
	int degree = 0;
	for (int i = 0; i < a.monomial_num; i++)
	{
		if (a.monomial[i].count() > degree)
			degree = a.monomial[i].count();
	}
	return degree;
}
Poly poly_multiply(Poly a, Poly b)  /* c = a AND b */
{
	Poly res;
	uint544 tmp;

	for (int i = 0; i < a.monomial_num; i++)
	{
		for (int j = 0; j < b.monomial_num; j++)
		{
			tmp = a.monomial[i] | b.monomial[j];
			remove_or_add_term(res, tmp);

		}
	}
	res.monomial_num = res.monomial.size();
	res.degree = poly_degree(res);
	return res;
}
Poly poly_add(Poly a, Poly b) /* c = a XOR b */
{
	Poly res = a;
	for (int i = 0; i < b.monomial_num; i++)
	{
		remove_or_add_term(res, b.monomial[i]);
	}
	res.monomial_num = res.monomial.size();
	res.degree = poly_degree(res);
	return res;
}

void state_initial(Poly *state) 
{
	int i;
	for (i = 0; i < 544; i++)
	{
		uint544 tmp;
		state[i].monomial_num = 1;
		state[i].degree = 1;
		state[i].monomial.push_back(tmp.set(i));
	}
}

void state_update(Poly* state)
{
	Poly a, b, c, t[5];

	t[0] = poly_add(state[65], state[92]);
	t[1] = poly_add(state[161], state[176]);
	t[2] = poly_add(poly_add(state[242], state[287]), state[415]);
	t[3] = state[415];
	t[4] = state[543];

	a = poly_multiply(state[285], state[286]);
	a = poly_add(t[2], poly_add(state[68], a));


	b = poly_multiply(state[90], state[91]);
	b = poly_add(t[0],poly_add(state[170], b));
	b = poly_add(b, state[543]);

	c = poly_multiply(state[174], state[175]);
	c = poly_add(t[1], poly_add(state[263], c));

	int i;
	for (i = 287; i > 0; i--) state[i] = state[i - 1];
	state[0]   = a;
	state[93]  = b;
	state[177] = c;  
	for (i = 543; i > 288; i--) state[i] = state[i - 1];
	state[288] = t[3];
	state[416] = t[4];
}
Poly key_stream(Poly* state)
{
	Poly t[3], z;
	t[0] = poly_add(state[65], state[92]);
	t[1] = poly_add(state[161], state[176]);
	t[2] = poly_add(poly_add(state[242], state[287]), state[415]);
	z = poly_add(poly_add(t[0], t[1]), t[2]);
	return z;
}

Monomial remove_no_max_term(Monomial monomial, uint544 low_deg_term)
{
	Monomial result = monomial;
	int flag = 0;
	for (int i = 0; i < monomial.size(); i++)
	{
		if ((monomial[i] & low_deg_term) == low_deg_term)
			break;
		else if ((monomial[i] & low_deg_term) == monomial[i])
		{
			Monomial::iterator it = find(result.begin(), result.end(), monomial[i]);
			result.erase(it);
			flag = 1;
		}
		else
			flag = 1;
	}
	if (flag) result.push_back(low_deg_term);
	return result;
}
void remove_no_DivPro_term(Poly& z)
{
	uint544 tmp;
	for (int i = 288; i < 416; i++) tmp[i] = 1;
	tmp.flip();
	for (int i = 0; i < z.monomial.size(); i++)
	{
		z.monomial[i] = z.monomial[i] & tmp;
	}
}
int get_max_poly(Poly z, int round)
{
	Monomial max_deg_monomial, low_deg_monomial;
	for (int i = 0; i < z.monomial_num; i++)
	{
		if (z.monomial[i].count() == z.degree)
			max_deg_monomial.push_back(z.monomial[i]);
		else 
			low_deg_monomial.push_back(z.monomial[i]);
	}
	Monomial max_monomial = max_deg_monomial;
	for (int i = 0; i < low_deg_monomial.size(); i++)
	{
		max_monomial = remove_no_max_term(max_monomial, low_deg_monomial[i]);
	}
	uint544 tmp;
	for (int i = 288; i < 416; i++) tmp[i] = 1;
	tmp.flip();
	/* Write the maximal terms of each round and its number into a py file. */
	char file_name[100];
	sprintf(file_name, "%d-round-maximal-polynomial.py", round);
	FILE* f = fopen(file_name, "w");
	fprintf(f, "## Maximal polynomial of %d-round output ##\n", round);
	fprintf(f, "## The number of maximal term: %lld ##\n", max_monomial.size());
	fprintf(f, "max_terms = [\n");
	for (int i = 0; i < max_monomial.size(); i++)
	{
		uint544 tmp_term = max_monomial[i] & tmp;
		int deg = tmp_term.count();
		int counter = 1;
		fprintf(f,"[");
		while (counter <= deg)
		{
			for (int j = 0; j < 544; j++)
			{
				if (tmp_term[j]) 
				{
					if (counter == deg) 
						fprintf(f,"%d", j);
					else 
						fprintf(f,"%d,", j);
					counter++;
				}
			}
		}
		if (i == (max_monomial.size() - 1))
			fprintf(f,"]\n");
		else
			fprintf(f,"],\n");
	}
	fprintf(f,"]\n");
	fclose(f);
	
	return max_monomial.size(); /* return the number of maximal terms */
}

void analyze_polynomial(int round)
{
	int NUM;
	Poly state[544], z;
	state_initial(state);
	for (int i = 1; i <= round; i++)
	{
		state_update(state);
		z = key_stream(state);
		/* Print the number of monomial in i-round output on the screen */
		printf("round = %4d, monomial_number = %d, ", i, z.monomial_num);
		remove_no_DivPro_term(z);
		NUM = get_max_poly(z,i);
		/* Print the number of maximal term in i-round output on the screen */
		printf("maximal_term_number = %d\n", NUM);
	};
}
int main()
{
	printf("Input rounds: ");
	int round;
	scanf("%d", &round);
	analyze_polynomial(round);
	printf("Maximal polynomial of each round has been written into the file!\n");
	return 0;
}