from gurobipy import *
from MAXTERMS import *
import datetime
class Trivium(object):
	"""docstring for Trivium"""
	def __init__(self, obj_round, cand_deg, max_term, f, file_name):
		super(Trivium, self).__init__()
		self.round = obj_round
		self.cand_deg = cand_deg
		self.term = max_term
		self.f = f
		self.file_name = file_name
		self.variables = []

	def flag_xor(self, flag1, flag2):
		if flag1 == 0:
			res = flag2
		elif flag1 == 1:
			if flag2 == 1:
				res = 0
			elif flag2 == 0:
				res = 1
			else:
				res = 2
		else:
			res = 2
		return res

	def flag_and(self, flag1, flag2):
		if flag1 == 0:
			res = 0
		elif flag1 == 1:
			res = flag2
		else:
			if flag2 == 0:
				res = 0
			else:
				res = 2
		return res

	def division_copy(self, div_src, div_dst1, div_dst2):
		self.f.write(div_src+" - "+div_dst1+" - "+div_dst2+" = 0\n")

	def division_xor(self, div_src1, div_src2, div_src3, div_src4, div_dst):
		src = [div_src1, div_src2, div_src3, div_src4]
		self.f.write(" + ".join(src)+" - "+div_dst+" = 0\n")

	def division_and(self, div_src1, div_src2, div_dst, flag_dst):
		if flag_dst == 0:
			self.f.write(div_dst+" = 0\n")
		self.f.write(div_dst+" - "+div_src1+" >= 0\n")
		self.f.write(div_dst+" - "+div_src2+" >= 0\n")
		self.f.write(div_dst+" - "+div_src1+" - "+div_src2+" <= 0\n")

	def initial_state(self):
		stated = []
		statef = []
		for i in range(93):
			stated.append("s"+str(i))
			self.f.write("s"+str(i)+" = 0\n")
			if i < 80:
				statef.append(2)
			else:
				statef.append(0)
		for i in range(93, 173):
			stated.append("s"+str(i))
			if i - 93 < 80:
				statef.append(2)
			else:
				self.f.write("s"+str(i)+" = 0\n")
				statef.append(0)
		for i in range(173, 288):
			stated.append("s"+str(i))
			self.f.write("s"+str(i)+" = 0\n")
			if i < 285:
				statef.append(0)
			else:
				statef.append(1)
		self.f.write(" + ".join(stated[i+93] for i in range(80))+" >= "+str(self.cand_deg+1)+"\n")
		self.variables += stated
		return (stated, statef)

	def state_update(self, stated, statef, t):
		copy_d = [["c"+str(t)+"_"+str(j)+"_"+str(i) for i in range(2)] for j in range(12)]
		and_d = ["a"+str(t)+"_"+str(i) for i in range(3)]
		xor_d = ["x"+str(t)+"_"+str(i) for i in range(3)]
		self.variables += and_d+xor_d

		copy_f = [[0 for i in range(2)] for j in range(12)]
		and_f = [0 for i in range(3)]
		xor_f = [0 for i in range(3)]

		# x = s[242]+s[287]+s[285]*s[286]+s[68] #
		# y = s[65]+s[92]+s[90]*s[91]+s[170]
		# z = s[161]+s[176]+s[174]*s[175]+s[263] #
		index = [242, 285, 286, 68, 65, 90, 91, 170, 161, 174, 175, 263]
		last = [287, 92, 176]
		for rgst in range(3):
			s = 4*rgst
			e = s+4
			for i in range(s,e):
				self.variables += copy_d[i]
				self.division_copy(stated[index[i]], copy_d[i][0], copy_d[i][1])
				stated[index[i]] = copy_d[i][1]
				copy_f[i][0] = statef[index[i]]
				copy_f[i][1] = statef[index[i]]
			and_f[rgst] = self.flag_and(copy_f[s+1][0],copy_f[s+2][0])
			self.division_and(copy_d[s+1][0],copy_d[s+2][0],and_d[rgst],and_f[rgst])
			self.division_xor(copy_d[s][0],stated[last[rgst]],copy_d[s+3][0],and_d[rgst],xor_d[rgst])
			xor_f[rgst] = self.flag_xor(copy_f[s][0],statef[last[rgst]])
			xor_f[rgst] = self.flag_xor(xor_f[rgst], copy_f[s+3][0])
			xor_f[rgst] = self.flag_xor(xor_f[rgst], and_f[rgst])

		for i in range(287):
			stated[287 - i] = stated[286 - i]
			statef[287 - i] = statef[286 - i]
		stated[0] = xor_d[0]
		statef[0] = xor_f[0]
		stated[93] = xor_d[1]
		statef[93] = xor_f[1]
		stated[177] = xor_d[2]
		statef[177] = xor_f[2]

	def output_division(self):
		(stated, statef) = self.initial_state()
		for t in range(self.round):
			self.state_update(stated,statef,t)
		for i in range(len(stated)):
			if i not in self.term:
				self.f.write(stated[i]+" = 0\n")
			else:
				self.f.write(stated[i]+" <= 1\n")

	def obj_function(self):
		self.f.write("Maximize\n")
		iv = ["s"+str(i+93) for i in range(80)]
		self.f.write(" + ".join(iv)+"\n")

	def constraints(self):
		self.f.write("Subject To\n")
		self.output_division()

	def var_type(self):
		self.f.write("Binary\n")
		self.f.write("\n".join(self.variables)+"\nEnd\n")

	def creat_model(self):
		self.obj_function()
		self.constraints()
		self.var_type()

	def solve_model(self):
		model = read(self.file_name)
		#model.Params.Threads = 30
		#model.Params.OutputFlag = 1
		model.optimize()
		if model.Status == 2:
			obj_var = model.getObjective()
			obj_value = obj_var.getValue()
			return int(obj_value)
		else:
			return 0
def main():
	file_name = "trivium.lp"
	t2 = 225
	for r in range(t2+1, 1153):
		t1 = r - t2
		degree = 0
		start = datetime.datetime.now()
		for term in max_terms:
			print("========================================= "+str(max_terms.index(term)+1)+" ====================================\n")
			f = open(file_name,"w")
			trivium = Trivium(t1, degree, term, f, file_name)
			trivium.creat_model()
			f.close()
			obj_value = trivium.solve_model()	
			if degree < obj_value:
				degree = obj_value
		end = datetime.datetime.now()
		fp = open("result.txt","a")
		fp.write("round = "+str(r)+", degree = "+str(degree)+", time = "+str(end-start)+" s\n")
		fp.close()	

if __name__ == '__main__':
	main()











