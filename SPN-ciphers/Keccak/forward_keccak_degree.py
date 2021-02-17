from gurobipy import*
import copy

class KECCAK(object):
	"""docstring for KECCAK"""
	def __init__(self, obj_round, input_div_wt, file_name, f):
		super(KECCAK, self).__init__()
		self.round = obj_round
		self.input_div_wt = input_div_wt
		self.file_name = file_name
		self.f = f
		self.variables = set()
		assert obj_round >= 1

	def get_variable(self, name, cur_round, flag):	
		if flag == 1:
			res = []
			for i in range(5):
				row = []
				for j in range(5):
					col = []
					for k in range(64):
						col.append(name+"_"+str(cur_round)+"_"+str(i*320+j*64+k))
					row.append(col)
					self.variables |= set(col)
				res.append(row)
			return res
		else:
			res = []
			for i in range(5):
				row = []
				for j in range(64):
					row.append(name+str(cur_round)+"_"+str(i*64+j))
				self.variables |= set(row)
				res.append(row)
			return res

	def div_copy_to2(self, src, dst1, dst2, flag):
		if flag == 1:
			for i in range(5):
				for j in range(5):
					for k in range(64):
						self.f.write(dst1[i][j][k]+" + "+dst2[i][j][k]+" - "+src[i][j][k]+" = 0\n")		
		else:
			for i in range(5):
				for j in range(64):
					self.f.write(dst1[i][j]+" + "+dst2[i][j]+" - "+src[i][j]+" = 0\n")	

	def div_xor2(self, src1, src2, src3, dst):		
		for k in range(64):
			self.f.write(dst[k]+" - "+src1[k]+" - "+src2[k]+" - "+src3[k]+" = 0\n")
			
	def div_xor5(self, src, dst):
		for j in range(64):
			self.f.write(" + ".join(src[k][j] for k in range(5))+" - "+dst[j]+" = 0\n")

	def rot(self, src, r):
		return [src[(i-r)%64] for i in range(64)]

	def theta_step(self,input,cur_round):
		copy_A0 = self.get_variable("ca0",cur_round,1)
		copy_A1 = self.get_variable("ca1",cur_round,1)
		self.div_copy_to2(input, copy_A0, copy_A1, 1)
		# xor #
		C = self.get_variable("c",cur_round,0)
		for i in range(5):
			self.div_xor5(copy_A0[i], C[i])

		copy_C0 = self.get_variable("cc0",cur_round,0)
		copy_C1 = self.get_variable("cc1",cur_round,0)
		self.div_copy_to2(C, copy_C0, copy_C1, 0)

		output = self.get_variable("b",cur_round,1)
		for row in range(5):
			for col in range(5):
				self.div_xor2(copy_A1[row][col], copy_C0[(row-1)%5],self.rot(copy_C1[(row+1)%5], 1),output[row][col])
		tmp = [[],[]]
		for row in range(5):
			for col in range(5):
				tmp[0] += input[row][col]
				tmp[1] += output[row][col]
		self.f.write(" + ".join(tmp[0])+" - "+" - ".join(tmp[1])+" = 0\n")
		return output

	def rho_step(self,input):
		offset = [[0,1,62,28,27],[36,44,6,55,20],[3,10,43,25,39],[41,45,15,21,8],[18,2,61,56,14]]
		output = []
		for i in range(5):
			tmp = []
			for j in range(5):
				tmp.append(self.rot(input[i][j],offset[j][i]))
			output.append(tmp)
		return output

	def pi_step(self,input):
		output = copy.deepcopy(input)	
		for i in range(5):
			for j in range(5):
				output[j][(2*i+3*j)%5] = input[i][j]
		return output

	def chi_step(self,input,cur_round):
		equ = [
			[1, 1, 1, 1, 1, -1, -1, -1, -1, -1, 0],
			[-1, -1, 0, -3, -2, 1, 3, 5, 3, 2, 0],
			[-3, 0, -5, -4, -1, 3, -2, -6, 4, 1, 13],
			[0, -3, -2, -1, -1, 5, 3, 2, 1, 3, 0],
			[-4, -1, -3, 0, -5, 4, 1, 3, -2, -6, 13],
			[0, -5, -4, -1, -3, -2, -6, 4, 1, 3, 13],
			[0, -2, 0, 1, 1, -3, 2, -2, -1, -2, 6],
			[0, 1, 1, 0, -2, -2, -1, -2, -3, 2, 6],
			[-3, -2, -1, -1, 0, 3, 2, 1, 3, 5, 0],
			[3, 3, 0, 0, 4, -3, -4, -2, -2, -4, 5],
			[0, 0, 4, 3, 3, -2, -2, -4, -3, -4, 5],
			[4, 3, 3, 0, 0, -4, -3, -4, -2, -2, 5],
			[-2, -1, -1, 0, -3, 2, 1, 3, 5, 3, 0],
			[-1, 0, -1, -1, 0, 0, 2, 1, 1, 0, 1],
			[-3, -3, 0, -5, -4, 1, 3, -2, -4, 4, 13],
			[-1, -2, -1, -1, 0, -2, 0, 1, 1, 0, 5],
			[1, 0, -1, 1, 1, -2, -2, 1, -2, -1, 4],
			[0, 1, 1, 1, 0, 0, -2, -1, -1, -1, 2],
			[0, -1, -2, -1, -1, 3, 3, 2, 1, 1, 0],
		]
		output = self.get_variable("s",cur_round,1)
		for i in range(5):
			for j in range(64):
				for e in equ:
					self.f.write(" + ".join(str(e[k])+" "+input[k][i][j] for k in range(5))+" + ")
					self.f.write(" + ".join(str(e[k+5])+" "+output[k][i][j] for k in range(5))+" >= "+str(-e[10])+"\n")
		return output

	def keccak_encrypt(self):
		state = self.get_variable("x",0,1)
		tmp = []
		for i in range(5):
			for j in range(5):
				tmp += state[i][j]
		self.f.write(" + ".join(tmp)+" = "+str(self.input_div_wt)+"\n")
		for cur_round in range(self.round):
			state = self.theta_step(state, cur_round)
			state = self.rho_step(state)
			state = self.pi_step(state)
			state = self.chi_step(state, cur_round)
		tmp = []
		for i in range(5):
			for j in range(5):
				tmp += state[i][j]
		self.f.write(" + ".join(tmp)+" - obj = 0\n")

	def obj_function(self):
		self.f.write("Minimize\nobj\n")

	def var_type(self):
		self.f.write("Binary\n")
		for var in self.variables:
			self.f.write(var+"\n")
		self.f.write("END\n")

	def creat_model(self):
		self.obj_function()
		self.f.write("Subject To\n")
		self.keccak_encrypt()
		self.var_type()

	def solve_model(self):
		model = read(self.file_name)
		model.optimize(mycallback)
		if model.Status == 2:
			obj = model.getObjective()
			value = obj.getValue()
			return int(value)
		else:
			return 0
bound = None

def mycallback(model,where):
	if where == GRB.Callback.MIP:
		objbst = model.cbGet(GRB.Callback.MIP_OBJBST)
		# objbnd = model.cbGet(GRB.Callback.MIP_OBJBND)
		if objbst <= bound:	# or objbnd > pos_degree:
			model.terminate()

def degree_evaluate(t, degree, round):
	global bound
	file_name = "forward-keccak.lp"
	bound = degree
	input_div_wt = degree
	output_div_wt = 0
	while output_div_wt <= bound and input_div_wt < 1600:
		input_div_wt += 1
		f = open(file_name,"w")
		keccak = KECCAK(t, input_div_wt, file_name, f)
		keccak.creat_model()		
		f.close()
		output_div_wt = keccak.solve_model()
	return input_div_wt-1

def main():
	## deg(G) = 1 if Round(G) = 0 ##
	round = int(input("Round(G): "))
	degree = int(input("deg(G): "))
	t = int(input("t: "))
	f = open("forward-result.txt","a")
	f.write("### t = %d ###\n"%t)
	f.write("round = %d, degree = %d\n"%(round, degree))
	f.close()
	while degree < 1599:
		degree = degree_evaluate(t,degree,round)
		round += t
		f = open("forward-result.txt","a")
		f.write("round = %d, degree = %d\n"%(round, degree))
		f.close()

if __name__ == '__main__':
	main()
