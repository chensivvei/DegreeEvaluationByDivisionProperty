from gurobipy import*
import copy
class inv_KNOT(object):
	"""docstring for inv_KNOT"""
	def __init__(self, round, input_dp_wt, file_name, f, word_size):
		super(inv_KNOT, self).__init__()
		self.round= round
		self.input_dp_wt = input_dp_wt
		self.file_name = file_name
		self.f = f
		self.word_size = word_size
		self.variables = set()

	def generate_variable(self, name, round):
		res = []
		for i in range(4):
			tmp = []
			for j in range(self.word_size):
				tmp.append(name+'_'+str(round)+'_'+str(i)+'_'+str(j))
			res.append(tmp)
			self.variables |= set(tmp)
		return res

	def inv_nonlinear_layer(self,input,round):
		equ = [[1, 1, 1, 1, -1, -1, -1, -1, 0],
				[-2, -1, -2, -3, 1, 2, 1, 3, 3],
				[-4, -1, -1, 3, -3, -1, 2, -2, 7],
				[0, 0, 2, 0, -1, -1, 0, -1, 1],
				[1, 0, 0, 3, -1, -2, -2, -1, 2],
				[-1, -3, -4, -2, 1, 1, 2, -1, 7],
				[-2, -1, -1, 0, 2, 4, 2, 3, 0],
				[-1, 1, 1, 0, -1, 1, -2, -3, 4],
				[1, -1, 0, 0, -1, -1, -2, 1, 3],
				[0, 1, 0, 0, -1, -2, 1, -1, 2],
				[1, 1, 3, 1, -1, -2, -2, -2, 1],
				[0, -1, 0, -1, 2, 1, 2, 2, 0],
				[2, 2, 0, 0, 0, -1, -1, -1, 1],
				[1, 0, 0, -1, -1, -1, 1, -2, 3],
				[0, -1, -1, 0, 0, 1, 1, 1, 1]]
		output = self.generate_variable('s',round)
		for i in range(self.word_size):
			for e in equ:
				self.f.write(" + ".join([str(e[j])+" "+input[3-j][i] for j in range(4)])+" + ")
				self.f.write(" + ".join([str(e[j+4])+" "+output[3-j][i] for j in range(4)]))
				self.f.write(" >= "+str(-e[8])+"\n")
		return output

	def inv_word_rotate(self, input):
		offset = [0, 1, 8, 25]
		if self.word_size == 128:
			offset[2] = 16
		elif self.word_size == 96:
			offset[3] = 55
		output = copy.deepcopy(input)
		for i in range(4):
			output[i] = [input[i][(j-offset[i])%self.word_size] for j in range(self.word_size)]
		return output

	def constraints(self):
		self.f.write("Subject To\n")
		state = self.generate_variable('x',0)
		self.f.write(" + ".join(state[0]+state[1]+state[2]+state[3])+" = "+str(self.input_dp_wt)+"\n")
		for i in range(self.round-1):
			state = self.inv_nonlinear_layer(state, i)
			state = self.inv_word_rotate(state)
		state = self.inv_nonlinear_layer(state, self.round - 1)
		self.f.write(" + ".join(state[0]+state[1]+state[2]+state[3])+" - obj = 0\n")

	def obj_function(self):
		self.f.write("Minimize\nobj\n")

	def var_type(self):
		self.f.write("Binary\n")
		for v in self.variables:
			self.f.write(v+"\n")
		self.f.write("END\n")

	def creat_model(self):
		self.obj_function()
		self.constraints()
		self.var_type()

	def solve_model(self):
		model = read(self.file_name)
		model.optimize(mycallback)
		if model.Status == 2:
			obj = model.getObjective()
			var = obj.getValue()
		else:
			var = 0
		return int(var)

bound = None
def mycallback(model,where):
	if where == GRB.Callback.MIP:
		objbst = model.cbGet(GRB.Callback.MIP_OBJBST)
		objbnd = model.cbGet(GRB.Callback.MIP_OBJBND)
		if objbst <= bound:	# or objbnd > pos_degree:
			model.terminate()
		# elif objbnd > bound:
		# 	model.Status = 2
		# 	obj = model.getObjective()
		# 	obj.getValue() = objbnd
		# 	model.terminate()


def degree_evaluate(t, degree, round, block_size):
	global bound
	file_name = "backward-knot%d.lp"%block_size
	bound = degree
	input_dp_wt = degree 
	output_dp_wt = 0
	while output_dp_wt <= degree and input_dp_wt < block_size:
		input_dp_wt += 1
		f = open(file_name,"w")
		knot = inv_KNOT(t, input_dp_wt, file_name, f, int(block_size/4))
		knot.creat_model()
		f.close()
		output_dp_wt = knot.solve_model()
	return input_dp_wt-1

def main():
	## deg(G) = 1 if Round(G) = 0 ##
	block_size = int(input("Block size (256, 384, 512): "))
	round = int(input("Round(G): "))
	degree = int(input("deg(G): "))
	t = int(input("t: "))
	f = open("backward%d-result.txt"%block_size,"a")
	f.write("### t = %d ###\n"%t)
	f.write("round = %d, degree = %d\n"%(round, degree))
	f.close()
	while degree < block_size - 1:
		degree = degree_evaluate(t,degree,round, block_size)
		round += t
		f = open("backward%d-result.txt"%block_size,"a")
		f.write("round = %d, degree = %d\n"%(round, degree))
		f.close()

if __name__ == '__main__':
	main()


